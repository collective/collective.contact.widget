from zope.publisher.browser import BrowserView


class RenderContentProvider(BrowserView):
    def __call__(self):
        return self.context.render()
