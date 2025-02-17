from kivymd.uix.widget import MDWidget


def hspacer(height: float):
    return MDWidget(
        size_hint_y=None,
        height=height,
    )
