import unittest
from airflow.decorators import dag
from datetime import datetime
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dags.utmb_flow import utmb_flow
import unittest
from unittest.mock import patch
from airflow.decorators import dag
from datetime import datetime
import os, sys


class TestUTMBFlow(unittest.TestCase):
    def test_dag_loading(self):
        """Test that the DAG can be properly loaded"""
        dag_obj = utmb_flow()
        self.assertIsNotNone(dag_obj)

    def test_dag_configuration(self):
        """Test DAG configuration parameters"""
        dag_obj = utmb_flow()
        self.assertEqual(dag_obj.schedule_interval, None)
        self.assertEqual(dag_obj.catchup, False)
        self.assertEqual(dag_obj.default_args["owner"], "Thibaut Donis")

    def test_task_dependencies(self):
        """Test that tasks are properly connected"""
        dag_obj = utmb_flow()
        tasks = dag_obj.tasks
        self.assertEqual(len(tasks), 4)  # Should have 4 tasks
        task_ids = [task.task_id for task in tasks]
        self.assertIn("utmb_extract", task_ids)
        self.assertIn("utmb_transform", task_ids)
        self.assertIn("utmb_load", task_ids)

    @patch("dags.utmb_flow.utmb_extract_clean_data")
    @patch("dags.utmb_flow.utmb_extract_data")
    @patch("dags.utmb_flow.utmb_extract_page")
    def test_utmb_extract_output(self, mock_page, mock_data, mock_clean):
        """
        Test that utmb_extract returns a correctly combined list.
        It patches the external dependencies to simulate predictable outputs.
        """

        # Setup: utmb_extract will process pages 1 to 3
        def page_side_effect(url):
            # Simply return the URL as a dummy page representation
            return url

        mock_page.side_effect = page_side_effect

        def data_side_effect(page):
            # Return a list with a single raw element string for the given page
            return [page + "_raw"]

        mock_data.side_effect = data_side_effect

        def clean_side_effect(data):
            # Perform a dummy cleaning by replacing '_raw' with '_clean'
            return [data[0].replace("_raw", "_clean")]

        mock_clean.side_effect = clean_side_effect

        # Retrieve the utmb_extract task callable from the DAG
        dag_obj = utmb_flow()
        utmb_extract_task = next(
            task for task in dag_obj.tasks if task.task_id == "utmb_extract"
        )
        # Call the underlying python function associated with the task
        result = utmb_extract_task.python_callable()

        expected = [

            "https://www.finishers.com/en/courses?page=1&series=utmbevent_clean",
            "https://www.finishers.com/en/courses?page=2&series=utmbevent_clean",
             "https://www.finishers.com/en/courses?page=3&series=utmbevent_clean"
        ]
        self.assertEqual(result, expected)

        if __name__ == "__main__":
            unittest.main()
