"""NAIRR-only extensions to Core-CMS ``taccsite_card`` (Card plugin)."""

from django.utils.translation import gettext_lazy as _

# Card form **Card style** value (``Style.class_name``); label is **Statistic**.
NAIRR_CARD_SKIN_STAT = 'card--stat'
_LEGACY_STAT_SKIN = 'c-card--stat'


def _patch_skin_modifier() -> None:
    import taccsite_card.utils as card_utils

    if getattr(card_utils, '_nairr_stat_skin_patched', False):
        return
    original = card_utils.class_name_to_skin_modifier

    def class_name_to_skin_modifier(class_name):
        if class_name in (NAIRR_CARD_SKIN_STAT, _LEGACY_STAT_SKIN):
            return NAIRR_CARD_SKIN_STAT
        return original(class_name)

    card_utils.class_name_to_skin_modifier = class_name_to_skin_modifier
    card_utils._nairr_stat_skin_patched = True


def register_nairr_card_skins() -> None:
    """Append **Statistic** (`card--stat`) to Card style choices and render hook."""
    import taccsite_card.constants as card_constants
    import taccsite_card.forms as card_forms

    base_choices = tuple(
        (value, label)
        for value, label in card_constants.CARD_SKIN_CLASS_NAME_CHOICES
        if value not in (NAIRR_CARD_SKIN_STAT, _LEGACY_STAT_SKIN)
    )
    extended = (*base_choices, (NAIRR_CARD_SKIN_STAT, _('Statistic')))
    card_constants.CARD_SKIN_CLASS_NAME_CHOICES = extended
    # ``forms`` imports choices at module load; keep its binding in sync.
    card_forms.CARD_SKIN_CLASS_NAME_CHOICES = extended
    _patch_skin_modifier()
