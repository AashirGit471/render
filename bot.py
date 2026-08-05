"""Appointments monitor bot"""

from datetime import datetime, timedelta
import threading
import queue
import time
import requests
from utils import logger, CONFIG, COOKIES, HEADERS, PAYLOAD

known_available_slots = set()
cache_lock = threading.Lock()


class MonitorBot:
    "A bot that monitors appointment slots and processes the data."

    def __init__(self):
        self.stop_event = threading.Event()
        self.data_queue = queue.Queue()
        self.payload_queue = queue.Queue()
        self.request_threads = []
        self.processor_thread = None
        self.status = "stopped"

    @property
    def running(self):
        "Check if the bot is currently running."
        return not self.stop_event.is_set()

    def start(self):
        "Start the bot and its worker threads."
        logger.info("Starting background worker.")

        if self.status != "stopped":
            self.status = "starting"
            logger.info("Old instance is still running, stopping it.")
            self.stop()
            time.sleep(1)

        self.status = "starting"
        # clear cache
        self.stop_event.clear()
        self.data_queue = queue.Queue()
        self.payload_queue = queue.Queue()
        self.processor_thread = None

        payloads = self.build_payload_list()
        logger.info("Total payloads build: %s", len(payloads))
        for payload in payloads:
            self.payload_queue.put(payload)

        max_workers = CONFIG["requests"]["max_concurrent_requests"]

        for worker_id in range(max_workers):
            thread = threading.Thread(
                target=self.request_worker,
                args=(worker_id,),
                daemon=True,
                name=f"request-worker-{worker_id}",
            )

            thread.start()
            self.request_threads.append(thread)

        self.processor_thread = threading.Thread(
            target=self.processor_worker,
            daemon=True,
            name="processor-worker",
        )
        self.processor_thread.start()
        logger.info("%s background worker(s) started.", max_workers)
        self.status = "running"

    def stop(self):
        "Stop the bot and its worker threads."
        logger.info("Stopping bot.")
        self.status = "stopping"
        self.stop_event.set()
        while True:
            if all(not thread.is_alive() for thread in self.request_threads) and (
                not self.processor_thread or not self.processor_thread.is_alive()
            ):
                break
            time.sleep(1)
        logger.info("All threads shutdown and bot stopped successfully.")
        self.status = "stopped"

    def request_worker(self, worker_id):
        "Worker that sends requests and puts the response in the data queue."

        while not self.stop_event.is_set():
            try:
                try:
                    payload = self.payload_queue.get(timeout=1)
                except queue.Empty:
                    continue

                retries = CONFIG["requests"]["max_retries"]
                for i in range(retries):
                    try:
                        response = requests.put(
                            url=CONFIG["targeted_website"]["endpoint"],
                            cookies=COOKIES,
                            headers=HEADERS,
                            json=payload,
                            timeout=CONFIG["requests"]["timeout"],
                            proxies=CONFIG.get("proxy"),
                        )
                        response.raise_for_status()
                        data = response.json()
                        break
                    except requests.exceptions.JSONDecodeError:
                        logger.error(
                            "[Worker %s] Invalid JSON response received. (%s/%s)",
                            worker_id,
                            i,
                            retries,
                        )

                    except requests.RequestException as exc:
                        logger.error(
                            "[Worker %s] %s | (%s/%s)",
                            worker_id,
                            exc,
                            i,
                            retries,
                        )
                    self._sleep(CONFIG["requests"]["retry_delay"])

                self.data_queue.put(
                    {
                        "worker_id": worker_id,
                        "status_code": response.status_code,
                        "data": data,
                        "payload": payload,
                    }
                )

            finally:
                self.payload_queue.put(payload)
                self.payload_queue.task_done()
                self._sleep(CONFIG["requests"]["recheck_interval"])

    def _sleep(self, interval):
        for _ in range(interval):
            if self.stop_event.is_set():
                break
            time.sleep(1)

    def generate_date_range(self, start_date, end_date):
        """Yields every date string between start_date and end_date inclusive, dd/mm/yyyy format."""
        start = datetime.strptime(start_date, "%d/%m/%Y")
        end = datetime.strptime(end_date, "%d/%m/%Y")

        current = start

        while current <= end:
            yield current.strftime("%d/%m/%Y")
            current += timedelta(days=1)

    def get_dates_to_check(self):
        """Merges explicit dates + date_range, dedupes, and returns them sorted chronologically."""
        dates = set(CONFIG.get("dates", []))
        date_range = CONFIG.get("date_range", {})

        if date_range.get("enabled"):
            generated_dates = self.generate_date_range(
                date_range["start"],
                date_range["end"],
            )
            dates.update(generated_dates)

        return sorted(
            dates,
            key=lambda value: datetime.strptime(value, "%d/%m/%Y"),
        )

    def build_payload_list(self):
        "Build a list of payload with each date to check."
        dates = self.get_dates_to_check()

        payload_list = []
        for date in dates:
            payload = PAYLOAD.copy()
            payload["datefrom"] = date
            payload_list.append(payload)

        return payload_list

    def processor_worker(self):
        "Process data from the queue and handle it accordingly."
        while not self.stop_event.is_set():
            try:
                item = self.data_queue.get(timeout=1)
            except queue.Empty:
                continue
            try:
                self.process_data(item)
            finally:
                self.data_queue.task_done()
        logger.info("Data processor worker stopped.")

    def process_data(self, item):
        "Process the data received from the request worker."
        logger.info(
            "Status: %s | Processing item from worker %s",
            item["status_code"],
            item["worker_id"],
        )

        payload = item["payload"]
        date_str = payload["datefrom"]
        data = item["data"]
        slots = data["returnobject"]["slots"]

        available_count = sum(1 for slot in slots if slot["isavailable"])
        logger.info("%s | %s/%s available", date_str, available_count, len(slots))

        for slot in slots:
            if slot["isavailable"]:
                self.handle_slot_available(date_str, slot)
            else:
                self.handle_slot_unavailable(date_str, slot)

    def slot_key(self, date_str, slot):
        """Builds the unique identity tuple for a slot: (date, periodid, starttime, endtime)."""
        return (
            date_str,
            slot["periodid"],
            slot["starttime"],
            slot["endtime"],
        )

    def handle_slot_available(self, date_str, slot):
        """Adds a newly-available slot to the cache and alerts, unless already known."""
        key = self.slot_key(date_str, slot)

        with cache_lock:
            if key in known_available_slots:
                return
            known_available_slots.add(key)

        message = (
            "🎉 SLOT AVAILABLE\n\n"
            f"Date: {date_str}\n"
            f"Time: {slot['starttime']} - {slot['endtime']}"
        )
        logger.info(message.replace("\n", " | "))
        self.send_telegram_message(message)

    def handle_slot_unavailable(self, date_str, slot):
        """Removes a slot from the cache and alerts, only if it was previously known available."""
        key = self.slot_key(date_str, slot)

        with cache_lock:
            if key not in known_available_slots:
                return
            known_available_slots.remove(key)

        message = (
            "❌ SLOT UNAVAILABLE\n\n"
            f"Date: {date_str}\n"
            f"Time: {slot['starttime']} - {slot['endtime']}"
        )

        logger.info(message.replace("\n", " | "))
        self.send_telegram_message(message)

    def send_telegram_message(self, message, error=False):
        """Sends a message to Telegram."""
        bot_token = CONFIG["telegram"]["bot_token"]
        dev_chat_id = CONFIG["telegram"]["dev_chat_id"]
        users_chat_ids = CONFIG["telegram"]["users_chat_ids"]

        # Error ki surat mein sirf dev ko message bhejo
        if error:
            chat_ids = [dev_chat_id]
        else:
            chat_ids = [dev_chat_id, *users_chat_ids]

        for chat_id in chat_ids:
            try:
                requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": message,
                    },
                    timeout=CONFIG["requests"]["timeout"],
                )
            except requests.exceptions.RequestException:
                logger.error("Failed to send telegram message to chat_id: %s", chat_id)
