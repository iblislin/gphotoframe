try:
    import cluttergtk
    import clutter
except ImportError:
    pass

class FadeAnimationTimeline(object):

    def __init__(self, actor, time=1000, start=0, end=255):

        self.timeline_fade_in  = FadeAnimation(actor, time, start, end)
        self.timeline_fade_out = FadeAnimation(actor, time, end, start)

    def fade_in(self):
        self.timeline_fade_in.start()

    def fade_out(self):
        self.timeline_fade_out.start()

class FadeAnimation(object):

    def __init__(self, actor, time=300, start=0, end=255):
        self.timeline = clutter.Timeline(time)
        self.alpha = clutter.Alpha(self.timeline, clutter.EASE_OUT_SINE)
        self.behaviour = clutter.BehaviourOpacity(
            alpha=self.alpha, opacity_start=start, opacity_end=end)
        self.behaviour.apply(actor)

    def start(self):
        self.timeline.start()
