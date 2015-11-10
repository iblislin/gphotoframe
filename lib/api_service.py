import signal
import os

from json import dumps
from twisted.web import resource


class APIServer(resource.Resource):
    isLeaf = True

    def __init__(self, photo=None, *args, **kwargs):
        if photo is None:
            raise Exception()

        self.photo = photo

        signal.signal(signal.SIGHUP, self.next_photo_handler)

        resource.Resource.__init__(self, *args, **kwargs)

    def render_GET(self, request):
        path = request.path

        if path.startswith('/cur') or path == '/':  # current
            return dumps(self.get_payload(-1))

        elif path.startswith('/his'):  # history
            ls = [{
                    'id': os.path.splitext(i['title'])[0],
                    'url': self.yande_re_url(os.path.splitext(i['title'])[0]),
                    'filename': i['title'],
                } for i in self.photo.queue]
            ls.reverse()
            return dumps(ls)

        else:
            return ''

    def get_payload(self, idx):
        img_id = self.img_id(-1)
        payload = {
            'id': img_id,
            'url': self.yande_re_url(img_id),
            'filename': self.full_filename(idx),
        }
        return payload

    def yande_re_url(self, id):
        return 'https://yande.re/post/show/{name}'.format(name=id)

    def img_id(self, idx):
        return self.photo.queue[idx]['title'].split('.')[0]

    def full_filename(self, idx):
        return self.photo.queue[idx]['title']

    def next_photo_handler(self, signum, frame):
        self.photo.next_photo()
