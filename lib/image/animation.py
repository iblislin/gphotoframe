try:
    from gi.repository import Clutter
except ImportError:
    from ..utils.nullobject import Null
    Clutter = Null()

class FadeAnimationTimeline(object):

    def __init__(self, actor, time=1000, start=0, end=255):

        self.timeline_fade_in  = FadeAnimation(actor, time, start, end)
        self.timeline_fade_out = FadeAnimation(actor, time, end, start)

    def fade_in(self):
        self.timeline_fade_in.start()

    def fade_out(self):
        self.timeline_fade_out.start()

class FadeAnimation(Clutter.Timeline):

     def __init__(self, actor, time=300, start=0, end=255):
         super(FadeAnimation, self).__init__()
         super(FadeAnimation, self).set_duration(time)

         alpha = Clutter.Alpha.new_full(
             self, Clutter.AnimationMode.EASE_OUT_SINE)
         self.behaviour = Clutter.BehaviourOpacity(
             alpha=alpha, opacity_start=start, opacity_end=end)
         self.behaviour.apply(actor)
