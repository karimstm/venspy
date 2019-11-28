import threading

class ThreadQueue():

    threadQueue = []
    def __init__(self, threads=4):
        self.workers = [False for i in range(threads)]
        self.threads = threads

    def monitor(self):
        while self.threadQueue:
            for i in range(self.threads):
                if self.workers[i] is not False and not self.workers[i].isAlive():
                    self.workers[i] = False
                if not self.workers[i]:
                    task = self.threadQueue.pop(0)
                    self.workers[i] = threading.Thread(target=task["func"], args=(task['params'], task["callBack"]))
                    self.workers[i].start()
                    break

    def addTask(self, func, params, callBack=None):
        self.threadQueue.append({
            "func": func,
            "params": params,
            "callBack": callBack
        })
        if len(self.threadQueue) == 1:
            threading.Thread(target=self.monitor, args=[]).start()