import sys
from PyQt5 import QtWidgets, QtCore


class ParameterInputDialog(QtWidgets.QDialog):
    def __init__(self, parameters, parent=None):
        super(ParameterInputDialog, self).__init__(parent)
        self.setWindowTitle("Enter Parameters")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.inputs = {}

        # Create an input field for each parameter
        for param in parameters:
            param_name = param.name
            param_type = param.type
            
            label = QtWidgets.QLabel(f"{param_name} ({param_type}):")
            if "Streamlines" in param_type:
                # File input for Streamlines
                line_edit = QtWidgets.QLineEdit()
                browse_button = QtWidgets.QPushButton("Browse")
                browse_button.clicked.connect(lambda _, le=line_edit: self.select_file(le))
                h_layout = QtWidgets.QHBoxLayout()
                h_layout.addWidget(line_edit)
                h_layout.addWidget(browse_button)
                self.layout.addWidget(label)
                self.layout.addLayout(h_layout)
                self.inputs[param_name] = line_edit
            else:
                # Default text input for other types
                line_edit = QtWidgets.QLineEdit()
                self.layout.addWidget(label)
                self.layout.addWidget(line_edit)
                self.inputs[param_name] = line_edit

        # OK and Cancel buttons
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

    def select_file(self, line_edit):
        """Open file dialog and set selected path to line_edit."""
        file_dialog = QtWidgets.QFileDialog()
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            line_edit.setText(file_path)

    def get_parameter_values(self):
        """Retrieve the input values from the dialog."""
        return {name: widget.text() for name, widget in self.inputs.items()}



