from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLabel

class TestResultsDialog(QDialog):
    """Dialog to display test results."""
    
    def __init__(self, parent, test_results):
        super().__init__(parent)
        self.test_results = test_results
        self.setWindowTitle("NetFlux5G Connection Test Results")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Add summary label
        summary = self.test_results.get('summary', {})
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        
        summary_text = f"Test Summary: {passed}/{total} tests passed ({failed} failed)"
        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(summary_label)
        
        # Create table for test results
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Test Name", "Result", "Details"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        # Add test results to table
        tests = self.test_results.get('tests', [])
        self.table.setRowCount(len(tests))
        
        for i, test in enumerate(tests):
            name_item = QTableWidgetItem(test.get('name', 'Unknown Test'))
            result_item = QTableWidgetItem(test.get('result', 'UNKNOWN'))
            details_item = QTableWidgetItem(test.get('message', ''))
            
            # Set color based on result
            if test.get('result') == 'PASS':
                result_item.setBackground(self.palette().color(self.palette().Base))
                result_item.setForeground(self.palette().color(self.palette().Text))
                result_item.setText("✓ PASS")
            else:
                result_item.setBackground(self.palette().color(self.palette().Base))
                result_item.setForeground(self.palette().color(self.palette().Text))
                result_item.setText("✗ FAIL")
            
            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, result_item)
            self.table.setItem(i, 2, details_item)
        
        layout.addWidget(self.table)
        
        # Add close button
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

def add_component_interaction_methods(main_window_class):
    """Add component interaction methods to the main window class."""
    
    def view_component_logs(self, component_id=None):
        """View logs for the selected component."""
        from component_utils import ComponentUtils
        
        if component_id is None:
            # Get currently selected component
            selected_ids = self.scene.selectedNodeIds()
            if not selected_ids:
                return
            component_id = selected_ids[0]
        
        ComponentUtils.view_logs_for_component(self, component_id)
    
    def open_component_terminal(self, component_id=None):
        """Open a terminal for the selected component."""
        from component_utils import ComponentUtils
        
        if component_id is None:
            # Get currently selected component
            selected_ids = self.scene.selectedNodeIds()
            if not selected_ids:
                return
            component_id = selected_ids[0]
        
        ComponentUtils.open_terminal_for_component(self, component_id)
    
    def restart_component(self, component_id=None):
        """Restart the selected component."""
        from component_utils import ComponentUtils
        
        if component_id is None:
            # Get currently selected component
            selected_ids = self.scene.selectedNodeIds()
            if not selected_ids:
                return
            component_id = selected_ids[0]
        
        ComponentUtils.restart_component(self, component_id)
    
    def show_test_results(self, test_results):
        """Show test results dialog."""
        dialog = TestResultsDialog(self, test_results)
        dialog.exec_()
    
    def handle_automation_finished(self, success, message):
        """Handle automation finished event."""
        if success:
            self.showCanvasStatus(f"Deployment completed successfully: {message}")
        else:
            self.showCanvasStatus(f"Deployment failed: {message}")
    
    # Add methods to the class
    main_window_class.view_component_logs = view_component_logs
    main_window_class.open_component_terminal = open_component_terminal
    main_window_class.restart_component = restart_component
    main_window_class.show_test_results = show_test_results
    main_window_class.handle_automation_finished = handle_automation_finished
    
    return main_window_class
