import logging
import os
from typing import Annotated, Optional
from __main__ import vtk, qt, slicer

import importlib
import inspect
import pkgutil
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)
from PyQt5 import QtWidgets, QtCore

# from slicer.ScriptedLoadableModule import ScriptedLoadableModuleWidget, VTKObservationMixin
from Scripts.TreeStructure import list_dipy_contents
from slicer import vtkMRMLScalarVolumeNode
# from Scripts.UI import DipyDialog
from numpydoc.docscrape import NumpyDocString

#
# DipyTools
#

dipy_structure = list_dipy_contents()


class DipyTools(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("DipyTools") 
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "MTP")]
        self.parent.contributors = ["Mahir Jain (IIT Mandi)"]  
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#DipyTools">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Mahir Jain IIT waale.
""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # DipyTools1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="DipyTools",
        sampleName="DipyTools1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "DipyTools1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="DipyTools1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="DipyTools1",
    )

    # DipyTools2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="DipyTools",
        sampleName="DipyTools2",
        thumbnailFileName=os.path.join(iconsPath, "DipyTools2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="DipyTools2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="DipyTools2",
    )


#
# DipyToolsParameterNode
#


@parameterNodeWrapper
class DipyToolsParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode



#
# DipyToolsWidget
#

class DipyToolsWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    @staticmethod
    def list_dipy_contents():
        dipy_structure = {}

        dipy_subpackages = ["io", "reconst", "segment", "tracking"]


        for subpackage_name in dipy_subpackages:
            full_subpackage_name = f"dipy.{subpackage_name}"
            try:
                subpackage_module = importlib.import_module(full_subpackage_name)
                dipy_structure[subpackage_name] = {}
            except ImportError:
                continue

            if hasattr(subpackage_module, "__path__"):
                for module_info in pkgutil.iter_modules(subpackage_module.__path__):
                    module_name = module_info.name
                    full_module_name = f"{full_subpackage_name}.{module_name}"
                    
                    try:
                        module = importlib.import_module(full_module_name)
                        dipy_structure[subpackage_name][module_name] = {"functions": [], "classes": {}}
                    except ImportError:
                        continue

                    for name, obj in inspect.getmembers(module, inspect.isfunction):
                        dipy_structure[subpackage_name][module_name]["functions"].append(name)

                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        class_methods = [func_name for func_name, func_obj in inspect.getmembers(obj, inspect.isfunction)]
                        dipy_structure[subpackage_name][module_name]["classes"][name] = class_methods

        return dipy_structure

    def setup(self) -> None:
        ScriptedLoadableModuleWidget.setup(self)

        self.dipy_structure = self.list_dipy_contents()

        self.label_module = qt.QLabel("Select DIPY Subpackage:")
        self.combo_module = qt.QComboBox()
        self.combo_module.addItems(list(self.dipy_structure.keys()))

        self.label_submodule = qt.QLabel("Select Submodule:")
        self.combo_submodule = qt.QComboBox()
        self.combo_submodule.setEnabled(False)

        self.label_class = qt.QLabel("Select Class or Function:")
        self.combo_class_func = qt.QComboBox()
        self.combo_class_func.setEnabled(False)

        self.label_method = qt.QLabel("Select Method (if applicable):")
        self.combo_method = qt.QComboBox()
        self.combo_method.setEnabled(False)

        self.layout.addWidget(self.label_module)
        self.layout.addWidget(self.combo_module)
        self.layout.addWidget(self.label_submodule)
        self.layout.addWidget(self.combo_submodule)
        self.layout.addWidget(self.label_class)
        self.layout.addWidget(self.combo_class_func)
        self.layout.addWidget(self.label_method)
        self.layout.addWidget(self.combo_method)

        self.combo_module.currentIndexChanged.connect(self.populate_submodules)
        self.combo_submodule.currentIndexChanged.connect(self.populate_classes_and_functions)
        self.combo_class_func.currentIndexChanged.connect(self.populate_methods)

        uiWidget = slicer.util.loadUI(self.resourcePath("UI/DipyTools.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        uiWidget.setMRMLScene(slicer.mrmlScene)
        self.logic = DipyToolsLogic()
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)
        self.initializeParameterNode()

    def populate_submodules(self):
        """Populate submodules based on the selected subpackage."""
        selected_module = self.combo_module.currentText
        submodules = self.dipy_structure.get(selected_module, {})

        self.combo_submodule.clear()
        self.combo_class_func.clear()
        self.combo_method.clear()
        self.combo_class_func.setEnabled(False)
        self.combo_method.setEnabled(False)

        if submodules:
            self.combo_submodule.addItems(list(submodules.keys()))
            self.combo_submodule.setEnabled(True)
        else:
            self.combo_submodule.setEnabled(False)

    def populate_classes_and_functions(self):
        selected_module = self.combo_module.currentText
        selected_submodule = self.combo_submodule.currentText

        self.combo_class_func.clear()
        self.combo_method.clear()
        self.combo_method.setEnabled(False)

        contents = self.dipy_structure.get(selected_module, {}).get(selected_submodule, {})

        if isinstance(contents, dict):
            functions = contents.get("functions", [])
            classes = list(contents.get("classes", {}).keys())
        else:
            functions = contents
            classes = []

        if functions or classes:
            self.combo_class_func.addItems(functions + classes)
            self.combo_class_func.setEnabled(True)
        else:
            self.combo_class_func.setEnabled(False)

    def populate_methods(self):
        selected_module = self.combo_module.currentText
        selected_submodule = self.combo_submodule.currentText
        selected_item = self.combo_class_func.currentText

        contents = self.dipy_structure.get(selected_module, {}).get(selected_submodule, {})

        self.combo_method.clear()

        if isinstance(contents, dict):
            if selected_item in contents.get("classes", {}):
                methods = contents["classes"][selected_item]
                self.combo_method.addItems(methods)
                self.combo_method.setEnabled(True)
            else:
                self.combo_method.setEnabled(False)
        else:
            self.combo_method.setEnabled(False)

    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: Optional[DipyToolsParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        self.ui.applyButton.enabled = True
    
    def selectFilePath(self, param_name, line_edit_widget):
        """Open a file dialog to select a file path."""
        file_dialog = qt.QFileDialog()
        file_dialog.setFileMode(qt.QFileDialog.ExistingFile)
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            line_edit_widget.setText(selected_file)
        
    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        
        # Get selected module, submodule, and function

        
        selected_module = self.combo_module.currentText
        selected_submodule = self.combo_submodule.currentText
        selected_class_func = self.combo_class_func.currentText
        selected_method = self.combo_method.currentText if self.combo_method.isEnabled() else None
        
        module = importlib.import_module(f"dipy.{selected_module}.{selected_submodule}")
        func = getattr(module, selected_class_func)

        if inspect.isclass(func):
            if selected_method:
                if hasattr(func, selected_method):
                    method = getattr(func, selected_method)
                    params = NumpyDocString(method.__doc__)
                else:
                    print("Error: Selected method not found in the class.")
                    return
            else:
                print("Error: No method selected for the class.")
                return

        else:
            params = NumpyDocString(func.__doc__)

        print(f"The function/class here is {func}")
        
        for parameter in params["Parameters"]:
            print(f"{parameter.name} : {parameter.type}")


        # slicer.util.infoDisplay(params["Parameters"], windowTitle=None, parent=None, standardButtons=None)
        
        
        self.param_widgets = []
        self.param_values = {}  # Dictionary to store the user's input values

        for parameter in params["Parameters"]:
            param_name = parameter.name
            param_type = parameter.type.lower()

            # Create a widget based on the parameter type

            # File path widget (for Streamlines, WM mask, etc.)
            if param_type == "streamlines" or "path" in param_name.lower():
                label = qt.QLabel(f"File Path for {param_name}:")
                path_widget = qt.QLineEdit()  # Editable field for path
                browse_button = qt.QPushButton("Browse...")
                browse_button.clicked.connect(lambda _, p=param_name, w=path_widget: self.selectFilePath(p, w))
                
                # Layout for file path input
                path_layout = qt.QHBoxLayout()
                path_layout.addWidget(path_widget)
                path_layout.addWidget(browse_button)

                # Add widgets and layout to the main layout
                self.layout.addWidget(label)
                self.layout.addLayout(path_layout)
                self.param_widgets.extend([label, path_widget, browse_button])
                self.param_values[param_name] = path_widget  # Store QLineEdit in param_values for later retrieval

            # Integer input widget
            elif "int" in param_type:
                label = qt.QLabel(f"Integer value for {param_name}:")
                int_widget = qt.QSpinBox()
                int_widget.setRange(-999999, 999999)  # Set a wide range for integers

                # Add widgets to the layout
                self.layout.addWidget(label)
                self.layout.addWidget(int_widget)
                self.param_widgets.extend([label, int_widget])
                self.param_values[param_name] = int_widget  # Store QSpinBox in param_values for later retrieval

            # Boolean checkbox widget
            elif "bool" in param_type:
                checkbox = qt.QCheckBox(f"{param_name} (True/False):")
                self.layout.addWidget(checkbox)
                self.param_widgets.append(checkbox)
                self.param_values[param_name] = checkbox  # Store QCheckBox in param_values for later retrieval

            # Fallback for unhandled types
            else:
                label = qt.QLabel(f"Value for {param_name} ({param_type}):")
                text_widget = qt.QLineEdit()

                # Add widgets to the layout
                self.layout.addWidget(label)
                self.layout.addWidget(text_widget)
                self.param_widgets.extend([label, text_widget])
                self.param_values[param_name] = text_widget  # Store QLineEdit in param_values for later retrieval
            
        param_values = {param.name: widget.value() if isinstance(widget, qt.QSpinBox) else
                        widget.isChecked() if isinstance(widget, qt.QCheckBox) else
                        widget.text() for param, widget in zip(params["Parameters"], self.param_widgets)}
        
        # Call the function/method and handle exceptions if they arise
        try:
            result = func(**param_values) if selected_method is None else getattr(func, selected_method)(**param_values)
            slicer.util.infoDisplay("Execution successful.")
        except Exception as e:
            slicer.util.errorDisplay(f"Execution failed: {e}")

                

#
# DipyToolsLogic
#


class DipyToolsLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return DipyToolsParameterNode(super().getParameterNode())

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLScalarVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "InputVolume": inputVolume.GetID(),
            "OutputVolume": outputVolume.GetID(),
            "ThresholdValue": imageThreshold,
            "ThresholdType": "Above" if invert else "Below",
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")


#
# DipyToolsTest
#


class DipyToolsTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_DipyTools1()

    def test_DipyTools1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("DipyTools1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = DipyToolsLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
