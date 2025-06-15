"""
Integration test for complex workflows that exercise multiple components of the system.

This test creates a project with requirements, specifications, and code, then
analyzes the project state, determines the optimal workflow, and executes the
workflow. It verifies that the workflow execution produces the expected results.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path

from devsynth.application.code_analysis.project_state_analyzer import ProjectStateAnalyzer
from devsynth.application.orchestration.adaptive_workflow import AdaptiveWorkflowManager
from devsynth.application.cli.cli_commands import init_cmd, inspect_cmd, spec_cmd, test_cmd, code_cmd


class TestComplexWorkflow:
    """Test complex workflows that exercise multiple components of the system."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir)
    
    def test_complex_workflow_with_inconsistent_state(self, temp_project_dir, monkeypatch):
        """
        Test a complex workflow with an inconsistent project state.
        
        This test simulates a complex workflow with an inconsistent project state:
        1. Initialize a new project
        2. Create requirements
        3. Create specifications that only partially cover the requirements
        4. Create code that only partially implements the specifications
        5. Analyze the project state (should detect inconsistencies)
        6. Use the adaptive workflow manager to determine the optimal workflow
        7. Execute the workflow
        8. Verify that the workflow execution improves the project state
        """
        # Set the current working directory to the temporary project directory
        original_dir = os.getcwd()
        os.chdir(temp_project_dir)
        
        try:
            # Step 1: Initialize a new project
            init_cmd(path=temp_project_dir)
            
            # Verify that the project was initialized
            assert os.path.exists(os.path.join(temp_project_dir, '.devsynth'))
            
            # Step 2: Create requirements
            requirements_dir = os.path.join(temp_project_dir, 'docs')
            os.makedirs(requirements_dir, exist_ok=True)
            
            requirements_content = """
            # Data Processing API Requirements
            
            ## Data Ingestion
            1. The system shall accept CSV file uploads
            2. The system shall accept JSON file uploads
            3. The system shall validate file formats before processing
            4. The system shall handle files up to 100MB in size
            
            ## Data Processing
            1. The system shall parse CSV files into structured data
            2. The system shall parse JSON files into structured data
            3. The system shall transform data according to user-defined rules
            4. The system shall aggregate data based on specified criteria
            
            ## Data Export
            1. The system shall export processed data as CSV
            2. The system shall export processed data as JSON
            3. The system shall provide a download link for exported data
            4. The system shall allow scheduling of regular exports
            """
            
            with open(os.path.join(requirements_dir, 'requirements.md'), 'w') as f:
                f.write(requirements_content)
            
            # Step 3: Create specifications that only partially cover the requirements
            specs_content = """
            # Data Processing API Specifications
            
            ## Data Ingestion API
            
            ### CSV Upload Endpoint
            - **Endpoint**: POST /api/upload/csv
            - **Description**: Uploads a CSV file for processing
            - **Request**:
              - Content-Type: multipart/form-data
              - Body: CSV file
            - **Response**:
              - 200 OK: File uploaded successfully
              - 400 Bad Request: Invalid file format
              - 413 Payload Too Large: File exceeds size limit
            
            ### JSON Upload Endpoint
            - **Endpoint**: POST /api/upload/json
            - **Description**: Uploads a JSON file for processing
            - **Request**:
              - Content-Type: multipart/form-data
              - Body: JSON file
            - **Response**:
              - 200 OK: File uploaded successfully
              - 400 Bad Request: Invalid file format
              - 413 Payload Too Large: File exceeds size limit
            
            ## Data Processing API
            
            ### Process CSV Endpoint
            - **Endpoint**: POST /api/process/csv
            - **Description**: Processes a previously uploaded CSV file
            - **Request**:
              - Content-Type: application/json
              - Body: Processing parameters
            - **Response**:
              - 200 OK: File processed successfully
              - 404 Not Found: File not found
              - 500 Internal Server Error: Processing error
            """
            
            with open(os.path.join(temp_project_dir, 'specs.md'), 'w') as f:
                f.write(specs_content)
            
            # Step 4: Create code that only partially implements the specifications
            src_dir = os.path.join(temp_project_dir, 'src')
            os.makedirs(src_dir, exist_ok=True)
            
            # Create a data_ingestion.py file with partial implementation
            data_ingestion_code = """
            class DataIngestion:
                def __init__(self, max_file_size=104857600):  # 100MB in bytes
                    self.max_file_size = max_file_size
                
                def upload_csv(self, file):
                    # Check file size
                    if len(file.read()) > self.max_file_size:
                        return {"status": "error", "message": "File exceeds size limit"}
                    
                    # Reset file pointer
                    file.seek(0)
                    
                    # Validate CSV format
                    try:
                        # Implementation for CSV validation
                        pass
                    except Exception as e:
                        return {"status": "error", "message": f"Invalid CSV format: {str(e)}"}
                    
                    # Store the file
                    # Implementation for file storage
                    
                    return {"status": "success", "message": "CSV file uploaded successfully"}
                
                def upload_json(self, file):
                    # Check file size
                    if len(file.read()) > self.max_file_size:
                        return {"status": "error", "message": "File exceeds size limit"}
                    
                    # Reset file pointer
                    file.seek(0)
                    
                    # Validate JSON format
                    try:
                        # Implementation for JSON validation
                        pass
                    except Exception as e:
                        return {"status": "error", "message": f"Invalid JSON format: {str(e)}"}
                    
                    # Store the file
                    # Implementation for file storage
                    
                    return {"status": "success", "message": "JSON file uploaded successfully"}
            """
            
            with open(os.path.join(src_dir, 'data_ingestion.py'), 'w') as f:
                f.write(data_ingestion_code)
            
            # Create tests directory with minimal tests
            tests_dir = os.path.join(temp_project_dir, 'tests')
            os.makedirs(tests_dir, exist_ok=True)
            
            test_data_ingestion_code = """
            import unittest
            from src.data_ingestion import DataIngestion
            
            class TestDataIngestion(unittest.TestCase):
                def setUp(self):
                    self.data_ingestion = DataIngestion()
                
                def test_upload_csv_file_too_large(self):
                    # Mock a file that's too large
                    class MockFile:
                        def read(self):
                            return b'x' * (104857600 + 1)  # 100MB + 1 byte
                        
                        def seek(self, position):
                            pass
                    
                    result = self.data_ingestion.upload_csv(MockFile())
                    self.assertEqual(result["status"], "error")
                    self.assertEqual(result["message"], "File exceeds size limit")
            
            if __name__ == '__main__':
                unittest.main()
            """
            
            with open(os.path.join(tests_dir, 'test_data_ingestion.py'), 'w') as f:
                f.write(test_data_ingestion_code)
            
            # Step 5: Analyze the project state
            analyzer = ProjectStateAnalyzer(temp_project_dir)
            initial_report = analyzer.analyze()
            
            # Verify that requirements were found
            assert initial_report['requirements_count'] > 0
            
            # Verify that specifications were found
            assert initial_report['specifications_count'] > 0
            
            # Verify that code files were found
            assert initial_report['code_count'] > 0
            
            # Verify that test files were found
            assert initial_report['test_count'] > 0
            
            # Verify that there are alignment issues
            assert initial_report['requirements_spec_alignment']['alignment_score'] < 1.0
            assert initial_report['spec_code_alignment']['implementation_score'] < 1.0
            
            # Step 6: Use the adaptive workflow manager to determine the optimal workflow
            adaptive_manager = AdaptiveWorkflowManager()
            workflow = adaptive_manager.determine_optimal_workflow(initial_report)
            
            # The optimal workflow should be either "specifications" or "code" due to the partial coverage
            assert workflow in ["specifications", "code"]
            
            # Step 7: Get suggested next steps
            suggestions = adaptive_manager.suggest_next_steps(temp_project_dir)
            
            # Verify that there are suggestions
            assert len(suggestions) > 0
            
            # Step 8: Mock the execution of commands
            def mock_execute_command(command, args):
                if command == "spec":
                    # Simulate generating complete specifications
                    complete_specs_content = specs_content + """
                    ### Process JSON Endpoint
                    - **Endpoint**: POST /api/process/json
                    - **Description**: Processes a previously uploaded JSON file
                    - **Request**:
                      - Content-Type: application/json
                      - Body: Processing parameters
                    - **Response**:
                      - 200 OK: File processed successfully
                      - 404 Not Found: File not found
                      - 500 Internal Server Error: Processing error
                    
                    ## Data Export API
                    
                    ### Export CSV Endpoint
                    - **Endpoint**: GET /api/export/csv
                    - **Description**: Exports processed data as CSV
                    - **Request**:
                      - Content-Type: application/json
                      - Body: Export parameters
                    - **Response**:
                      - 200 OK: Data exported successfully
                      - 404 Not Found: No data to export
                      - 500 Internal Server Error: Export error
                    
                    ### Export JSON Endpoint
                    - **Endpoint**: GET /api/export/json
                    - **Description**: Exports processed data as JSON
                    - **Request**:
                      - Content-Type: application/json
                      - Body: Export parameters
                    - **Response**:
                      - 200 OK: Data exported successfully
                      - 404 Not Found: No data to export
                      - 500 Internal Server Error: Export error
                    """
                    with open(os.path.join(temp_project_dir, 'specs.md'), 'w') as f:
                        f.write(complete_specs_content)
                    return {"status": "success"}
                elif command == "code":
                    # Simulate generating complete code
                    data_processing_code = """
                    class DataProcessing:
                        def __init__(self):
                            pass
                        
                        def process_csv(self, file_id, parameters):
                            # Implementation for CSV processing
                            return {"status": "success", "message": "CSV file processed successfully"}
                        
                        def process_json(self, file_id, parameters):
                            # Implementation for JSON processing
                            return {"status": "success", "message": "JSON file processed successfully"}
                    """
                    with open(os.path.join(src_dir, 'data_processing.py'), 'w') as f:
                        f.write(data_processing_code)
                    
                    data_export_code = """
                    class DataExport:
                        def __init__(self):
                            pass
                        
                        def export_csv(self, data_id, parameters):
                            # Implementation for CSV export
                            return {"status": "success", "message": "Data exported as CSV successfully"}
                        
                        def export_json(self, data_id, parameters):
                            # Implementation for JSON export
                            return {"status": "success", "message": "Data exported as JSON successfully"}
                    """
                    with open(os.path.join(src_dir, 'data_export.py'), 'w') as f:
                        f.write(data_export_code)
                    return {"status": "success"}
                return {"status": "error", "message": f"Unknown command: {command}"}
            
            # Patch the execute_command method
            monkeypatch.setattr(adaptive_manager, 'execute_command', mock_execute_command)
            
            # Step 9: Execute the adaptive workflow
            result = adaptive_manager.execute_adaptive_workflow(temp_project_dir)
            
            # Verify that the workflow execution was successful
            assert result["status"] == "success"
            
            # Step 10: Analyze the project state again
            final_report = analyzer.analyze()
            
            # Verify that the alignment scores have improved
            assert final_report['requirements_spec_alignment']['alignment_score'] > initial_report['requirements_spec_alignment']['alignment_score']
            assert final_report['spec_code_alignment']['implementation_score'] > initial_report['spec_code_alignment']['implementation_score']
            
            # Print the initial and final alignment scores for debugging
            print(f"Initial requirements-spec alignment: {initial_report['requirements_spec_alignment']['alignment_score']}")
            print(f"Final requirements-spec alignment: {final_report['requirements_spec_alignment']['alignment_score']}")
            print(f"Initial spec-code alignment: {initial_report['spec_code_alignment']['implementation_score']}")
            print(f"Final spec-code alignment: {final_report['spec_code_alignment']['implementation_score']}")
            
        finally:
            # Restore the original working directory
            os.chdir(original_dir)


if __name__ == "__main__":
    pytest.main(["-v", "test_complex_workflow.py"])
