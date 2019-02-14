
import sys

import unittest2

import mitogen.service

import testlib


class FetchTest(testlib.RouterMixin, testlib.TestCase):
    klass = mitogen.service.FileService

    def replyable_msg(self, **kwargs):
        recv = mitogen.core.Receiver(self.router, persist=False)
        msg = mitogen.core.Message(
            src_id=mitogen.context_id,
            reply_to=recv.handle,
            **kwargs
        )
        msg.router = self.router
        return recv, msg

    def test_unauthorized(self):
        service = self.klass(self.router)
        recv, msg = self.replyable_msg()
        service.fetch(
            path='/etc/shadow',
            sender=None,
            msg=msg,
        )
        e = self.assertRaises(mitogen.core.CallError,
            lambda: recv.get().unpickle())
        expect = service.unregistered_msg % ('/etc/shadow',)
        self.assertTrue(expect in e.args[0])

    if sys.platform == 'darwin':
        ROOT_GROUP = 'wheel'
    else:
        ROOT_GROUP = 'root'

    def _validate_response(self, resp):
        self.assertTrue(isinstance(resp, dict))
        self.assertEquals('root', resp['owner'])
        self.assertEquals(self.ROOT_GROUP, resp['group'])
        self.assertTrue(isinstance(resp['mode'], int))
        self.assertTrue(isinstance(resp['mtime'], float))
        self.assertTrue(isinstance(resp['atime'], float))
        self.assertTrue(isinstance(resp['size'], int))

    def test_path_authorized(self):
        recv = mitogen.core.Receiver(self.router)
        service = self.klass(self.router)
        service.register('/etc/passwd')
        recv, msg = self.replyable_msg()
        service.fetch(
            path='/etc/passwd',
            sender=recv.to_sender(),
            msg=msg,
        )
        self._validate_response(recv.get().unpickle())

    def test_root_authorized(self):
        recv = mitogen.core.Receiver(self.router)
        service = self.klass(self.router)
        service.register_prefix('/')
        recv, msg = self.replyable_msg()
        service.fetch(
            path='/etc/passwd',
            sender=recv.to_sender(),
            msg=msg,
        )
        self._validate_response(recv.get().unpickle())

    def test_prefix_authorized(self):
        recv = mitogen.core.Receiver(self.router)
        service = self.klass(self.router)
        service.register_prefix('/etc')
        recv, msg = self.replyable_msg()
        service.fetch(
            path='/etc/passwd',
            sender=recv.to_sender(),
            msg=msg,
        )
        self._validate_response(recv.get().unpickle())

    def test_prefix_authorized_abspath_bad(self):
        recv = mitogen.core.Receiver(self.router)
        service = self.klass(self.router)
        service.register_prefix('/etc')
        recv, msg = self.replyable_msg()
        service.fetch(
            path='/etc/foo/bar/../../../passwd',
            sender=recv.to_sender(),
            msg=msg,
        )
        self.assertEquals(None, recv.get().unpickle())

    def test_prefix_authorized_abspath_bad(self):
        recv = mitogen.core.Receiver(self.router)
        service = self.klass(self.router)
        service.register_prefix('/etc')
        recv, msg = self.replyable_msg()
        service.fetch(
            path='/etc/../shadow',
            sender=recv.to_sender(),
            msg=msg,
        )
        e = self.assertRaises(mitogen.core.CallError,
            lambda: recv.get().unpickle())
        expect = service.unregistered_msg % ('/etc/../shadow',)
        self.assertTrue(expect in e.args[0])


if __name__ == '__main__':
    unittest2.main()
