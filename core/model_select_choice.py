from django.db import models


class FOLLOW_UP_STAGE(models.TextChoices):
    STAGE_01 = "stage_01"
    STAGE_02 = "stage_02"
    STAGE_03 = "stage_03"
    STAGE_04 = "stage_04"
    STAGE_05 = "stage_05"
    STAGE_06 = "stage_06"

class LEAD_STAGE(models.TextChoices):
    LOST = "lost"
    RESPONSE = "response"
    FOLLOW_UP = "follow_up"
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"
    CONVERTED = "converted"
