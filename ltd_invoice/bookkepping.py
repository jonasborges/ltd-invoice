import logging
import os
import urllib.parse

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import Select

from ltd_invoice.pdf_parse import Invoice


class Bookkeper:
    def __init__(self) -> None:
        logging.info("Creating Bookkeper")
        self._is_logged = False
        self.driver = self.get_webdriver()
        logging.info("Selenium window size %s", self.driver.get_window_size())
        self.driver.maximize_window()
        self.base_url = os.environ["BOOKKEPPING_PLATFORM_URL"]
        self.driver.get(self.base_url)
        logging.info("Bookkeper created!")

    def __del__(self):
        try:
            self.driver.close()
        except AttributeError:
            # can't close a driver that's not there
            pass

    @staticmethod
    def get_webdriver() -> WebDriver:
        selenium_webdriver = os.environ["SELENIUM_WEBDRIVER"]

        if selenium_webdriver == "hub":
            return webdriver.Remote(
                command_executor=os.environ["SELENIUM_HUB"],
                desired_capabilities=DesiredCapabilities.FIREFOX,
            )
        elif selenium_webdriver == "local":
            return webdriver.Firefox()
        else:
            raise ValueError(
                f"Invalid SELENIUM_WEBDRIVER envvar: {selenium_webdriver}"
            )

    def login(self) -> None:
        user = os.environ["BOOKKEPPING_PLATFORM_USER"]
        password = os.environ["BOOKKEPPING_PLATFORM_PASS"]
        self.driver.find_element_by_name("UserName").send_keys(user)
        self.driver.find_element_by_name("UserPassword").send_keys(password)
        self.driver.find_element_by_id(
            "kt_login_singin_form_submit_button"
        ).click()
        self._is_logged = True

    def open_invoice_page(self) -> None:
        self.driver.get(
            urllib.parse.urljoin(self.base_url, "/salesinvoice/show")
        )

    def fill_client_data(
        self,
        client_name: str,
        invoice_details: str,
        invoice_date: str,
        due_date: str,
    ) -> None:
        client_dropdown = Select(self.driver.find_element_by_id("client"))
        client_dropdown.select_by_visible_text(client_name)

        self.driver.find_element_by_id("INVOICE_NOTE").send_keys(
            invoice_details
        )

        invoice_date_elem = self.driver.find_element_by_id("INVOICE_DATE")
        self.driver.execute_script(
            "arguments[0].removeAttribute('readonly','readonly')",
            invoice_date_elem,
        )
        invoice_date_elem.send_keys(invoice_date)

        due_on_elem = self.driver.find_element_by_id("INVOICE_DUE_ON")
        self.driver.execute_script(
            "arguments[0].removeAttribute('readonly','readonly')", due_on_elem
        )
        due_on_elem.send_keys(due_date)

    def fill_service_data(
        self,
        service_type: str,
        work_description: str,
        rate_type: str,
        quantity: str,
        rate_value: str,
        vat_percent: str,
    ) -> None:
        service_type_dropdown = Select(
            self.driver.find_element_by_id("Service")
        )
        service_type_dropdown.select_by_visible_text(service_type)

        rate_type_dropdown = Select(self.driver.find_element_by_id("Type"))
        rate_type_dropdown.select_by_visible_text(rate_type)

        rate_type_dropdown = Select(self.driver.find_element_by_id("Vat"))
        rate_type_dropdown.select_by_visible_text(f"{vat_percent}%")

        self.driver.find_element_by_id("Workdescription").send_keys(
            work_description
        )
        self.driver.find_element_by_id("Quantity").send_keys(quantity)
        self.driver.find_element_by_id("Rate").send_keys(rate_value)

    def fill_internal_note(self, text: str) -> None:
        self.driver.find_element_by_id("CUSTOMER_NOTE").send_keys(text)

    def confirm_submit_popup(self) -> None:
        self.driver.execute_script("window.scrollTo(0, 0);")

        self.driver.find_element_by_id("1").click()

        self.driver.find_element_by_class_name("swal2-confirm").click()

    def submit_invoice(self) -> None:

        self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )
        self.driver.find_element_by_id("btnSaveInvoice").click()
        self.confirm_submit_popup()

    def register_invoice(self, invoice: Invoice) -> None:
        if not self._is_logged:
            self.login()
        self.open_invoice_page()
        self.fill_client_data(
            client_name=invoice.client_name,
            invoice_details=f"Sheet: {invoice.timesheet_id}\nInvoice number: {invoice.invoice_number}",
            invoice_date=invoice.invoice_date,
            due_date=invoice.payment_due_date,
        )
        self.fill_service_data(
            service_type="Timesheet",
            work_description="Week work",
            rate_type="Hours",
            quantity=invoice.hours_worked,
            rate_value=invoice.hour_rate,
            vat_percent=invoice.vat_rate,
        )

        self.fill_internal_note(invoice.internal_note)
        self.submit_invoice()
