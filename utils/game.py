import random
from time import sleep
from threading import Thread

class game:
    def __init__(self,msg_id,difficulty):
        self.difficulty = difficulty
        self.number = random.randint(1,difficulty)
        timer = Thread(target=self.timer)
        timer.start()
        self.msg_id = [msg_id]

    def timer(self):
        self.time = 0
        self.stop = True
        while self.time < 450 and self.stop:
            sleep(0.1)
            self.time+=1
        print("timer_stop")

    def IsGaming(self):
        if self.time != 0:
            return True
        else:
            return False

    def Guess(self,number):
        print(self.number)
        if number > self.difficulty or number < 0:
            return f"無效的答案\n剩餘{int(45 - self.time/10)}秒"
        if number == self.number:
            self.stop = False
            if self.time == 450:
                return f"你猜對啦!\n答案就是{self.number}\n但可惜時間已經到囉~"
            else:
                return f"你猜對啦!\n答案就是{self.number}!!!"
        else:
            if self.number > number:
                if self.number <= number + 5 and self.number - 5 <= number:
                    return f"答案很接近了!\n在{number}以上\n剩餘{int(45 - self.time/10)}秒"
                else:
                    return f"數字太小了~\n在{number}以上\n剩餘{int(45 - self.time/10)}秒"
            else:
                if self.number >= number - 5 and self.number + 5 >= number:
                    return f"答案很接近了!\n在{number}以下\n剩餘{int(45 - self.time/10)}秒"
                else:
                    return f"數字太大了~在{number}以下\n剩餘{int(45 - self.time/10)}秒"