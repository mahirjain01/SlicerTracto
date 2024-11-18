import sys
import dipy
import warnings
from TreeStructure import list_dipy_contents
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QComboBox, QLabel

warnings.filterwarnings('ignore') 

dipy_structure = list_dipy_contents()

class DipyDialog(QDialog):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("DIPY Module Selector")
        self.layout = QVBoxLayout()
        
        self.label_module = QLabel("Select DIPY Subpackage:")
        self.combo_module = QComboBox()
        self.combo_module.addItems(dipy_structure.keys())
        
        self.label_submodule = QLabel("Select Submodule:")
        self.combo_submodule = QComboBox()
        self.combo_submodule.setEnabled(False)
        
        self.label_class = QLabel("Select Class or Function:")
        self.combo_class_func = QComboBox()
        self.combo_class_func.setEnabled(False)
        
        self.label_method = QLabel("Select Method (if applicable):")
        self.combo_method = QComboBox()
        self.combo_method.setEnabled(False)
        
        self.layout.addWidget(self.label_module)
        self.layout.addWidget(self.combo_module)
        self.layout.addWidget(self.label_submodule)
        self.layout.addWidget(self.combo_submodule)
        self.layout.addWidget(self.label_class)
        self.layout.addWidget(self.combo_class_func)
        self.layout.addWidget(self.label_method)
        self.layout.addWidget(self.combo_method)
        
        self.setLayout(self.layout)
        
        self.combo_module.currentIndexChanged.connect(self.populate_submodules)
        self.combo_submodule.currentIndexChanged.connect(self.populate_classes_and_functions)
        self.combo_class_func.currentIndexChanged.connect(self.populate_methods)
    
    def populate_submodules(self):
        selected_module = self.combo_module.currentText()
        submodules = dipy_structure[selected_module]
        
        self.combo_submodule.clear()
        self.combo_class_func.clear()
        self.combo_method.clear()
        self.combo_class_func.setEnabled(False)
        self.combo_method.setEnabled(False)
        
        if submodules:
            self.combo_submodule.addItems(submodules.keys())
            self.combo_submodule.setEnabled(True)
        else:
            self.combo_submodule.setEnabled(False)
    
    def populate_classes_and_functions(self):
        selected_module = self.combo_module.currentText()
        selected_submodule = self.combo_submodule.currentText()
        
        self.combo_class_func.clear()
        self.combo_method.clear()
        self.combo_method.setEnabled(False)
        
        contents = dipy_structure[selected_module].get(selected_submodule, {})
        
        functions = contents.get("functions", [])
        classes = contents.get("classes", {}).keys()
        
        if functions or classes:
            self.combo_class_func.addItems(list(functions) + list(classes))
            self.combo_class_func.setEnabled(True)
        else:
            self.combo_class_func.setEnabled(False)
    
    def populate_methods(self):
        selected_module = self.combo_module.currentText()
        selected_submodule = self.combo_submodule.currentText()
        selected_item = self.combo_class_func.currentText()
        
        contents = dipy_structure[selected_module].get(selected_submodule, {})
        self.combo_method.clear()
        
        if selected_item in contents.get("classes", {}):
            methods = contents["classes"][selected_item]
            self.combo_method.addItems(methods)
            self.combo_method.setEnabled(True)
        else:
            self.combo_method.setEnabled(False)


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     dialog = DipyDialog()
#     dialog.show()
#     sys.exit(app.exec_())
