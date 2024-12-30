from LocalManager.Algos import algo1

class LocalManager:
    def __init__(self):
        pass

    def execute(self, subjectName, algo, approxMaskPathFilePath, fodfFilePath):
        if algo == 'algo1':
            algo1.run(subjectName=subjectName, approxMaskPathFilePath=approxMaskPathFilePath, fodfFilePath=fodfFilePath)
        elif algo == 'algo2':
            pass
            # algo2.run(approxMaskPathFilePath=approxMaskPathFilePath, fodfFilePath=fodfFilePath)