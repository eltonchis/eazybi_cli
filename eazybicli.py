"""EazyBiCli: Module for automation of eazyBI Account definitions.

This module provides the EazyBiCli class used to interface with the eazyBI CLI tool
to manage and extract eazyBI entities:
    - Accounts
    - Sources with definitions
    - Reports with definitions
    - Dashboards with definitions

It requires the eazyBI CLI binary to be installed on the execution environment.
Ref: https://docs.eazybi.com/eazybi/set-up-and-administer/eazybi-cli

"""

import platform
import subprocess
import re
import json
import logging

logger = logging.getLogger(__name__)

class EazyBiCliError(Exception):
    """Raised when an eazyBI CLI command fails or its output cannot be used."""

    def __init__(
        self,
        message: str,
        *,
        command: str = "",
        ) -> None:
        super().__init__(message)
        self.command = command or ""
        
class EazyBiCli:
    """This class will be used to automate eazyBI CLI interactions on background
    """
    
    CLASS_VERSION: str = "1.0.0"
    
    def __init__(self, eazybi_url: str, login_timeout: int = 30, timeout: int = 5 ) -> None:
        """Initialize a new eazyBI CLI object

        Args:
            eazybi_url (str): The eazyBI base URL used for login.
            login_timeout (int): number of seconds to approve login
            timeout (int): number of seconds to end process if not completed
        """
        self.eazybi_url = eazybi_url
        self.login_timeout = login_timeout
        self.timeout = timeout
        # Select OS
        self.os_name: str = platform.system()
        # Login on init 
        self._login()

    def _login(self) -> None:
        """ login on url 
        """
        command =["eazybi", "auth", "login", "--base-url", self.eazybi_url]
        print(" ".join(command))
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                timeout=self.login_timeout,
                check=True,
                encoding="utf-8"
                )
            print(result.stdout, result.stderr)
        except FileNotFoundError as exc:
            raise EazyBiCliError(
                "The 'eazybi' CLI binary was not found in PATH.",
                command=' '.join(command),
                ) from exc
        except subprocess.TimeoutExpired as exc:
            raise EazyBiCliError(
                f"Command timed out after {self.login_timeout} seconds: {' '.join(command)}",
                command=' '.join(command),
                ) from exc
        except subprocess.CalledProcessError as exc:
            raise EazyBiCliError(
                f"Error: {exc.stderr}, Command failed with exit code {exc.returncode}: {' '.join(command)}",
                command=' '.join(command)
                ) from exc
            
    def run_command(self, command: list[str]) -> str:
        """ Run a eazyBI CLI command and return its stdout.

        Args:
            command (list): Command and arguments, e.g. ["eazybi", "accounts", "list"].

        Returns:
            str: The standard output of the executed command.
        """
        # select flags
        flags = subprocess.CREATE_NO_WINDOW if self.os_name == "Windows" else 0
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                timeout=self.timeout,
                check=True,
                encoding="utf-8",
                creationflags=flags
                )
        except FileNotFoundError as exc:
            raise EazyBiCliError(
                "The eazybiCLI binary was not found in PATH.",
                command=' '.join(command),
                ) from exc
        except subprocess.TimeoutExpired as exc:
            raise EazyBiCliError(
                f"Command timed out after {self.timeout} seconds: {' '.join(command)}",
                command=' '.join(command),
                ) from exc
        except subprocess.CalledProcessError as exc:
            raise EazyBiCliError(
                f"Error: {exc.stderr}, Command failed with exit code {exc.returncode}: {' '.join(command)}",
                command=' '.join(command)
                ) from exc

        if result.stdout:
            return result.stdout
        elif result.stderr:
            raise EazyBiCliError(f"{result.stderr} {' '.join(command)}",command=' '.join(command))
        else:
            return ""
        
    def parse_text_table(self, text: str) -> list[dict]:
        """ Parse Text Tables output from commands
        
        Args:
            text (str): text table output from eazyBI CLI

        Returns:
            list[dict]: A list of python dictionaries with the data of the Text table [{"COLUMN":"Row Value"}]
        """
        # get all text lines
        lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        
        # if result is empty return empty list
        if not lines:
            return []
        
        # split headers from data lines
        header, *data_lines = lines
        
        # get all headers
        names = re.findall(r"\S+", header)
        
        # get columns index for start and end (slices)
        starts = [m.start() for m in re.finditer(r"\S+", header)]
        ends = starts[1:] + [None]  # each column runs until the next header starts

        # loop through data to append dicts in list
        records = []
        for line in data_lines:
            # loop through headers and slices to add elements to dict
            record = {}
            for name, start, end in zip(names, starts, ends):
                value = line[start:end].strip()
                record[name] = value or None  # empty cells become None
            records.append(record)
        return records

    @staticmethod
    def print_percent(listlen: int, iternum: int) -> None:
        """ print percentage of processed list

        Args:
            listlen (int): length of the list being processed
            iternum (int): iteration number (list index + 1 )
        """
        # select number of steps to print 
        if listlen <= 2 or iternum < 1:
            return
        elif listlen <= 20:
            steps = 2
        elif listlen <= 200:
            steps = 4
        elif listlen <= 1000:
            steps = 10
        else:
            steps = 20
        # print only on specific steps
        if (iternum % (listlen // steps)) == 0:
            percent = (iternum * 100) // listlen
            print(f"{iternum} of {listlen}, {percent}% completed")
        
    def get_accounts(self, keyword: str = "") -> list[dict]:
        """ enlist EazyBI Accounts

        Args:
            keyword (str): keyword to filter accounts by text in NAME
            
        Returns:
            list[dict]: A list of python dictionaries
        """
        command = ['eazybi', 'accounts', 'list']
        result = self.run_command(command)
        account_list = self.parse_text_table(result)
        # if no keyword return complete list else filter by keyword
        if keyword == "":
            return account_list
        else:
            return [i for i in account_list if keyword in (i.get("NAME") or "")]

    def get_sources(self, account: str) -> list[dict]:
        """enlist account sources

        Args:
            account (str): account ID

        Returns:
            list[dict]: A list of python dictionaries with the sources data
        """
        command = ["eazybi", "source-applications", "list", "-a", account]
        result = self.run_command(command)
        return self.parse_text_table(result)

    def get_source_def(self, account: str, source: str) -> dict:
        """get source definition json and return as dict

        Args:
            account (str): account ID
            source (str): source ID

        Returns:
            dict: A python dict from the json definition
        """
        command = ["eazybi", "source-applications", "export-definition", source, "-a", account]
        result = self.run_command(command)
        try:
            return json.loads(result)
        except json.JSONDecodeError as exc:
            raise EazyBiCliError(
                f"Invalid JSON returned for {command}: {exc}",
                command=' '.join(command),
                ) from exc

    def get_reports(self, account: str) -> list[dict]:
        """enlist account reports

        Args:
            account (str): account ID
            
        Returns:
            list[dict]: A list of python dictionaries with the reports data
        """
        command = ["eazybi", "reports", "list", "-a", account]
        result = self.run_command(command)
        return self.parse_text_table(result)

    def get_report_def(self, account: str, report: str) -> dict:
        """get report definition json and return as dict

        Args:
            account (str): account ID
            report (str): report ID
            
        Returns:
            dict: A python dict from the json definition
        """
        command = ["eazybi", "reports", "export-definition", report, "-a", account]
        result = self.run_command(command)
        try:
            return json.loads(result)
        except json.JSONDecodeError as exc:
            raise EazyBiCliError(
                f"Invalid JSON returned for {command}: {exc}",
                command=' '.join(command),
                ) from exc

    def get_dashboards(self, account: str) -> list[dict]:
        """enlist account dashboards

        Args:
            account (str): account ID
                        
        Returns:
            list[dict]: A list of python dictionaries with the dashboards data
        """
        command = ["eazybi", "dashboards", "list", "-a", account]
        result = self.run_command(command)
        return self.parse_text_table(result)

    def get_dashboard_def(self, account: str, dashboard: str) -> dict:
        """get dashboard definition json and return as dict

        Args:
            account (str): account ID
            dashboard (str): dashboard ID

        Returns:
            dict: A python dict from the json definition
        """
        command = ["eazybi", "dashboards", "export-definition", dashboard, "-a", account]
        result = self.run_command(command)
        try:
            return json.loads(result)
        except json.JSONDecodeError as exc:
            raise EazyBiCliError(
                f"Invalid JSON returned for {command}: {exc}",
                command=' '.join(command),
                ) from exc

    def get_all_def(self, keyword: str = "") -> list[dict]:
        """get all definitions (source, reports, dashboards) from accounts

        Args:
            keyword (str): keyword to filter accounst by text in NAME

        Returns:
            list[dict]: A list of python dictionaries with the accounts metadata
            and json definitions for:
            - sources
            - reports
            - dashboards
        """
        accounts = self.get_accounts(keyword)

        for acc in accounts:
            try:
                acc_id = acc.get("ID", "")
                
                print(f"Fetching Account {acc_id} {acc.get('NAME')} Sources")
                acc["SOURCES"] = self.get_sources(acc_id)
                
                list_len = len(acc["SOURCES"])
                for j, src in enumerate(acc["SOURCES"]):
                    src["DEFINITION"] = self.get_source_def(acc_id, src.get("ID", ""))
                    self.print_percent(list_len, (j + 1))
                    
                print(f"Fetching Account {acc.get('ID')} {acc.get('NAME')} Reports")
                acc["REPORTS"] = self.get_reports(acc_id)
                
                list_len = len(acc["REPORTS"])
                for j, rep in enumerate(acc["REPORTS"]):
                    rep["DEFINITION"] = self.get_report_def(acc_id, rep.get("ID", ""))
                    self.print_percent(list_len, (j + 1))

                print(f"Fetching Account {acc.get('ID')} {acc.get('NAME')} Dashboards")
                acc["DASHBOARDS"] = self.get_dashboards(acc_id)
                
                list_len = len(acc["DASHBOARDS"])
                for j, dsh in enumerate(acc["DASHBOARDS"]):
                    dsh["DEFINITION"] = self.get_dashboard_def(acc_id, dsh.get("ID", ""))
                    self.print_percent(list_len, (j + 1))
            except EazyBiCliError as exc:
                logger.warning("Skipping account %s (%s): %s", acc_id, acc.get("NAME"), exc)
                acc["ERROR"] = str(exc)

        return accounts

if __name__ == "__main__":
    print("Testing")

    # Example
    ezBIurl = r"https://jira.example.com/plugins/servlet/eazybi"
    eazyBI = EazyBiCli(ezBIurl)
    print(f"Test: {eazyBI.os_name}")
    accounts = eazyBI.get_accounts("AccountKeyword")
    account_sources = eazyBI.get_sources("AccountID")
    account_reports = eazyBI.get_reports("AccountID")
    report_definition = eazyBI.get_report_def("AccountID","ReportID")
    accounts_definitions =  eazyBI.get_all_def("AccountKeyword")
    
    
