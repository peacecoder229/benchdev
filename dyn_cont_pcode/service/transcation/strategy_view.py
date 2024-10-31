from setting import Setting
# from controller import Controller
from strategy import model_based_round_robin_controller


class StratergyViewController:
    Conf = {}
    Strategy = None

    def __init__(self, conf):
        self.Conf = conf

    def build_config(self):
        conf = self.Conf
        c = Setting(
            PR_COS=conf['PR_COS'],
            BE_COS=conf['BE_COS'],
            PR_cores=conf["PR_cores"],
            BE_cores=conf['BE_cores'],
            platform='skx'
        )

        self.Strategy = model_based_round_robin_controller.ModelBasedRoundRobinController(
            c.control_knobs, 100)

    def change_strategy(self):
        try:
            controller = Controller()
            controller.set_strategy(self.Strategy)

            return True
        except:
            return False
