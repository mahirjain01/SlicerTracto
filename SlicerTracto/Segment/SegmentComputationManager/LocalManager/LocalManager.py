from SegmentComputationManager.LocalManager.Algos.quickBundlesAlgo import QuickBundlesAlgo
from SegmentComputationManager.LocalManager.Algos.quickBundlesX import QuickBundlesXAlgo

import os
from SegmentComputationManager.baseManager import BaseManager


class LocalManager(BaseManager):
    def __init__(self):
        pass

    def execute(self, algo, trkPath, segmentedTrkFolderPath):
        if algo == 'QuickBundles':
            self.quicBundles = QuickBundlesAlgo(trkPath=trkPath, segmentedTrkFolderPath=segmentedTrkFolderPath)
            self.quicBundles.run()
        if algo == "QuickBundlesX":
            self.quicBundlesX = QuickBundlesXAlgo(trkPath=trkPath, segmentedTrkFolderPath=segmentedTrkFolderPath)
            self.quicBundlesX.run()

            

        