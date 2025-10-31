from django.db import models

# delivered, unique_opened, opened, click
# soft_bounce, hard_bounce, invalid_email, error, deferred
# spam, unsubscribed, blocked

class FOLLOW_UP_STAGE(models.TextChoices):
    STAGE_01 = "stage_01"           # sent/delivered
    STAGE_02 = "stage_02"           # delivered 24–48h+, still no open (nudge)
    STAGE_03 = "stage_03"           # opened, no click (warm)
    STAGE_04 = "stage_04"           # clicked (hot)
    STAGE_05 = "stage_05"           # replied/meeting intent (sales handoff)
    STAGE_06 = "stage_06"           # closed (stop—either converted or disqualified)

class LEAD_STAGE(models.TextChoices):
    LOST = "lost"                   # spam, invalid, hardBounce, softBounce, deferred
    RESPONSE = "response"           # click
    NOT_RESPONSE = "not_response"   # delivered
    FOLLOW_UP = "follow_up"         # opened/uniqueOpened
    QUALIFIED = "qualified"         
    NOT_QUALIFIED = "not_qualified" # unsubscribed, blocked
    CONVERTED = "converted"         

class EmailTemplatetype(models.TextChoices):
    HEADER_HOOK = "header_hook"
    CONTENT_HOOK = "content_hook"
    FOOTER_HOOK = "footer_hook"
    SIGNATURE_HOOK = "signature_hook"

class MailConfigType(models.TextChoices):
    SMTP = "smtp"
    API = "api"
