try:
    from gi.repository import Clutter, GtkClutter
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
        self.timeline = Clutter.Timeline.new(time)
        self.alpha = Clutter.Alpha.new_full(self.timeline, 
                                       Clutter.AnimationMode.EASE_OUT_SINE)

        self.behaviour = Clutter.BehaviourOpacity(
            alpha=self.alpha, opacity_start=start, opacity_end=end)
        self.behaviour.apply(actor)

    def start(self):
        self.timeline.start()
