import torch
from pt_lognormal import LognormalDiffStroke
from action_plan import ActionPlan
from pt_action_plan import DiffActionPlan


def fine_tune(vanilla_plan):
	pytorch_plan = DiffActionPlan(vanilla_plan)

	# Now run gradient descent on the params of pytorch_plan.
