from FodfComputationManager.LocalManager.Algos.generateFodf import GenerateFODF
import os
from FodfComputationManager.baseManager import BaseManager


class LocalManager(BaseManager):
    def __init__(self):
        pass

    def execute(self, subjectName, algo, inputFolderPath, outputFolderPath):
        if algo == 'Scilpy':
            diffusionPath, whiteMaskPath, bvalPath, bvecPath = self.getDipyInputs(folderPath=inputFolderPath)
            generateFodf = GenerateFODF(subjectName=subjectName, diffusionPath=diffusionPath, whiteMaskPath=whiteMaskPath, bvalPath=bvalPath, bvecPath=bvecPath, outputFolderPath=outputFolderPath)
            generateFodf.run()
            