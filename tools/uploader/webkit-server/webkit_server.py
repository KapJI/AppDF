"""
Python bindings for the `webkit-server <https://github.com/niklasb/webkit-server/>`_
"""

import sys, os
import subprocess
import re
import socket
import atexit
import json
import time

# path to the `webkit_server` executable
SERVER_EXEC = os.path.abspath(os.path.join(os.path.dirname(__file__), 'webkit_server'))


class SelectionMixin(object):
    """ Implements a generic XPath selection for a class providing a
    ``_get_xpath_ids`` and a ``get_node_factory`` method. """

    def css(self, css):
        """ Returns all nodes matching the given CSSv3 expression. """
        return [self.get_node_factory().create(node_id)
                        for node_id in self._get_css_ids(css).split(",")
                        if node_id]

    def at_css(self, css):
        """ Returns the first node matching the given CSSv3
        expression or ``None``. """
        return self._first_or_none(self.css(css))

    def at_xpath(self, xpath):
        """ Returns the first node matching the given XPath 2.0 expression or ``None``.
        """
        return self._first_or_none(self.xpath(xpath))

    def xpath(self, xpath):
        """ Finds another node by XPath originating at the current node. """
        return [self.get_node_factory().create(node_id)
                for node_id in self._get_xpath_ids(xpath).split(",")
                if node_id]

    def parent(self):
        """ Returns the parent node. """
        return self.at_xpath('..')

    def children(self):
        """ Returns the child nodes. """
        return self.xpath('*')

    def form(self):
        """ Returns the form wherein this node is contained or ``None``. """
        return self.at_xpath("ancestor::form")

    def _first_or_none(self, list):
        return list[0] if list else None

# default timeout values
DEFAULT_WAIT_INTERVAL = 0.5
DEFAULT_WAIT_TIMEOUT = 10
DEFAULT_AT_TIMEOUT = 5

class WaitTimeoutError(Exception):
    """ Raised when a wait times out """

class WaitMixin(SelectionMixin):
    """ Mixin that allows waiting for conditions or elements. """

    def wait_for(self,
                condition,
                interval = DEFAULT_WAIT_INTERVAL,
                timeout = DEFAULT_WAIT_TIMEOUT):
        """ Wait until a condition holds by checking it in regular intervals.
        Raises ``WaitTimeoutError`` on timeout. """

        start = time.time()

        # at least execute the check once!
        while True:
            try:
                res = condition()
                if res:
                    return res
            except Exception as e:
                print e
            # timeout?
            if time.time() - start > timeout:
                break

            # wait a bit
            time.sleep(interval)

        # timeout occured!
        raise WaitTimeoutError, "wait_for timed out"

    def wait_for_safe(self, *args, **kw):
        """ Wait until a condition holds and return
        ``None`` on timeout. """
        try:
            return self.wait_for(*args, **kw)
        except WaitTimeoutError:
            return None

    def wait_while(self, condition, *args, **kw):
        """ Wait while a condition holds. """
        return self.wait_for(lambda: not condition(), *args, **kw)

    def at_css(self, css, timeout = DEFAULT_AT_TIMEOUT, **kw):
        """ Returns the first node matching the given CSSv3 expression or ``None``
        if a timeout occurs. """
        return self.wait_for_safe(lambda: super(WaitMixin, self).at_css(css),
                                                            timeout = timeout,
                                                            **kw)

    def at_xpath(self, xpath, timeout = DEFAULT_AT_TIMEOUT, **kw):
        """ Returns the first node matching the given XPath 2.0 expression or ``None``
        if a timeout occurs. """
        return self.wait_for_safe(lambda: super(WaitMixin, self).at_xpath(xpath),
                                                            timeout = timeout,
                                                            **kw)

class NodeFactory(object):
    """ Implements the default node factory.

    `client` is the associated client instance. """

    def __init__(self, client):
        self.client = client

    def create(self, node_id):
        return Node(self.client, node_id)


class NodeError(Exception):
    """ A problem occured within a ``Node`` instance method. """
    pass

class Node(WaitMixin):
    """ Represents a DOM node in our Webkit session.

    `client` is the associated client instance.

    `node_id` is the internal ID that is used to identify the node when communicating
    with the server. """

    def __init__(self, client, node_id):
        super(Node, self).__init__()
        self.client = client
        self.node_id = node_id

    def text(self):
        """ Returns the inner text (*not* HTML). """
        return self._invoke("text")

    def get_bool_attr(self, name):
        """ Returns the value of a boolean HTML attribute like `checked` or `disabled`
        """
        val = self.get_attr(name)
        return val is not None and val.lower() in ("true", name)

    def get_attr(self, name):
        """ Returns the value of an attribute. """
        return self._invoke("attribute", name)

    def set_attr(self, name, value):
        """ Sets the value of an attribute. """
        self.exec_script("node.setAttribute(%s, %s)" % (repr(name), repr(value)))

    def value(self):
        """ Returns the node's value. """
        if self.is_multi_select():
            return [opt.value() for opt in self.xpath(".//option") if opt["selected"]]
        else:
            return self._invoke("value")

    def set(self, value):
        """ Sets the node content to the given value (e.g. for input fields). """
        def _set():
            self._invoke("set", value)
            return True
        self.wait_for(_set)

    def path(self):
        """ Returns an XPath expression that uniquely identifies the current node. """
        return self._invoke("path")

    def submit(self):
        """ Submits a form node. """
        self.eval_script("node.submit()")

    def eval_script(self, js):
        """ Evaluate arbitrary Javascript with the ``node`` variable bound to the
        current node. """
        return self.client.eval_script(self._build_script(js))

    def exec_script(self, js):
        """ Execute arbitrary Javascript with the ``node`` variable bound to
        the current node. """
        self.client.exec_script(self._build_script(js))

    def _build_script(self, js):
        return "var node = Capybara.nodes[%s]; %s;" % (self.node_id, js)

    def select_option(self):
        """ Selects an option node. """
        self._invoke("selectOption")

    def unselect_options(self):
        """ Unselects an option node (only possible within a multi-select). """
        if self.xpath("ancestor::select")[0].is_multi_select():
            self._invoke("unselectOption")
        else:
            raise NodeError, "Unselect not allowed."

    def _simple_mouse_event(self, event_name):
        """ Fires a simple mouse event such as ``mouseover``, ``mousedown`` or
        ``mouseup``. `event_name` specifies the event to trigger. """
        self.exec_script("""
            var ev = document.createEvent('MouseEvents');
            ev.initEvent(%s, true, false);
            node.dispatchEvent(ev);
            """ % repr(event_name))

    def _left_click(self):
        self._simple_mouse_event('mousedown');
        self._simple_mouse_event('mouseup');
        self._invoke("leftClick")
        return True        

    def left_click(self):
        """ Left click the current node. """
        self.wait_for(self._left_click)

    def click(self):
        #elf.left_click()
        self.exec_script("node.click()")

    def _double_click(self):
        self._invoke("doubleClick")
        return True

    def double_click(self):
        """ Double click the current node. """
        self.wait_for(self__double_click)

    def drag_to(self, element):
        """ Drag the node to another one. """
        self._invoke("dragTo", element.id)

    def tag_name(self):
        """ Returns the tag name of the current node. """
        return self._invoke("tagName")

    def is_visible(self):
        """ Checks whether the current node is visible. """
        return self._invoke("visible") == "true"

    def is_attached(self):
        """ Checks whether the current node is actually existing on the currently
        active web page. """
        return self._invoke("isAttached") == "true"

    def is_selected(self):
        """ is the ``selected`` attribute set for this node? """
        return self.get_bool_attr("selected")

    def is_checked(self):
        """ is the ``checked`` attribute set for this node? """
        return self.get_bool_attr("checked")

    def is_disabled(self):
        """ is the ``disabled`` attribute set for this node? """
        return self.get_bool_attr("disabled")

    def is_multi_select(self):
        """ is this node a multi-select? """
        return self.tag_name() == "select" and self.get_bool_attr("multiple")

    def _get_css_ids(self, css):
        """ Implements a mechanism to get a list of node IDs for an relative CSS
        query. """
        return self._invoke("findCssWithin", css)

    def _get_xpath_ids(self, xpath):
        """ Implements a mechanism to get a list of node IDs for an relative XPath
        query. """
        return self._invoke("findXpathWithin", xpath)

    def get_node_factory(self):
        """ Returns the associated node factory. """
        return self.client.get_node_factory()

    def __repr__(self):
        return "<Node #%s>" % self.path()

    def _invoke(self, cmd, *args):
        return self.client.issue_node_cmd(cmd, self.node_id, *args)     

class Client(WaitMixin):
    """ Wrappers for the webkit_server commands.

    If `connection` is not specified, a new instance of ``ServerConnection`` is
    created.

    `node_factory_class` can be set to a value different from the default, in which
    case a new instance of the given class will be used to create nodes. The given
    class must accept a client instance through its constructor and support a
    ``create`` method that takes a node ID as an argument and returns a node object.
    """

    def __init__(self,
                connection = None,
                node_factory_class = NodeFactory):
        super(Client, self).__init__()
        self.conn = connection or ServerConnection()
        self._node_factory = node_factory_class(self)
        self.set_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36")

    def visit(self, url):
        """ Goes to a given URL. """
        self.conn.issue_command("Visit", url)

    def body(self):
        """ Returns the current DOM as HTML. """
        return self.conn.issue_command("Body")

    def url(self):
        """ Returns the current location. """
        return self.conn.issue_command("CurrentUrl")

    def set_header(self, key, value):
        """ Sets a HTTP header for future requests. """
        self.conn.issue_command("Header", key, value)

    def reset(self):
        """ Resets the current web session. """
        self.conn.issue_command("Reset")

    def status_code(self):
        """ Returns the numeric HTTP status of the last response. """
        return int(self.conn.issue_command("Status"))

    def headers(self):
        """ Returns a dict of the last HTTP response headers. """
        return dict([tuple(header.split(": ", 1))
                    for header in self.conn.issue_command("Headers").split("\n")])

    def eval_script(self, expr):
        """ Evaluates a piece of Javascript in the context of the current page and
        returns its value. """
        ret = self.conn.issue_command("Evaluate", expr)
        return json.loads("[%s]" % ret)[0]

    def exec_script(self, script):
        """ Executes a piece of Javascript in the context of the current page. """
        self.conn.issue_command("Execute", script)

    def render(self, path, width = 1024, height = 1024):
        """ Renders the current page to a PNG file (viewport size in pixels). """
        self.conn.issue_command("Render", path, width, height)

    def set_cookie(self, cookie):
        """ Sets a cookie for future requests (must be in correct cookie string
        format). """
        self.conn.issue_command("SetCookie", cookie)

    def clear_cookies(self):
        """ Deletes all cookies. """
        self.conn.issue_command("ClearCookies")

    def cookies(self):
        """ Returns a list of all cookies in cookie string format. """
        return [line.strip()
                for line in self.conn.issue_command("GetCookies").split("\n") if line.strip()]

    def set_error_tolerant(self, tolerant=True):
        """ Sets or unsets the error tolerance flag in the server. If this flag
        is set, dropped requests or erroneous responses will not lead to an error! """
        self.conn.issue_command("SetErrorTolerance", "true" if tolerant else "false")

    def set_proxy(self, host = "localhost",
                port = 0,
                user = "",
                password = ""):
        """ Sets a custom HTTP proxy to use for future requests. """
        self.conn.issue_command("SetProxy", host, port, user, password)

    def clear_proxy(self):
        """ Resets custom HTTP proxy (use none in future requests). """
        self.conn.issue_command("ClearProxy")

    def issue_node_cmd(self, *args):
        """ Issues a node-specific command. """
        return self.conn.issue_command("Node", *args)

    def get_node_factory(self):
        """ Returns the associated node factory. """
        return self._node_factory

    def _get_css_ids(self, css):
        """ Implements a mechanism to get a list of node IDs for an CSS query. """
        return self.conn.issue_command("FindCss", css)

    def _get_xpath_ids(self, xpath):
        """ Implements a mechanism to get a list of node IDs for an absolute XPath
        query. """
        return self.conn.issue_command("FindXpath", xpath)

    def _normalize_attr(self, attr):
        """ Transforms a name like ``auto_load_images`` into ``AutoLoadImages``
        (allows Webkit option names to blend in with Python naming). """
        return ''.join(x.capitalize() for x in attr.split("_"))


class NoX11Error(Exception):
    """ Raised when the Webkit server cannot connect to X. """

class Server(object):
    """ Manages a Webkit server process. If `binary` is given, the specified
    ``webkit_server`` binary is used instead of the included one. """

    def __init__(self, binary = None):
        binary = binary or SERVER_EXEC
        self._server = subprocess.Popen([binary, '--ignore-ssl-errors'],
                                        stdin    = subprocess.PIPE,
                                        stdout = subprocess.PIPE,
                                        stderr = subprocess.PIPE)
        output = self._server.stdout.readline()
        try:
            self._port = int(re.search("port: (\d+)", output).group(1))
        except AttributeError:
            raise NoX11Error, "Cannot connect to X. You can try running with xvfb-run."

        # on program termination, kill the server instance
        atexit.register(self.kill)

    def kill(self):
        """ Kill the process. """
        self._server.kill()
        self._server.wait()

    def connect(self):
        """ Returns a new socket connection to this server. """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", self._port))
        return sock

default_server = None
def get_default_server():
    """ Returns a singleton Server instance (possibly after creating it, if it
    doesn't exist yet). """
    global default_server
    if not default_server:
        default_server = Server()
    return default_server


class NoResponseError(Exception):
    """ Raised when the Webkit server does not respond. """

class InvalidResponseError(Exception):
    """ Raised when the Webkit server signaled an error. """

class EndOfStreamError(Exception):
    """ Raised when the Webkit server closed the connection unexpectedly. """

class ServerConnection(object):
    """ A connection to a Webkit server.

    `server` is a server instance or `None` if a singleton server should be connected
    to (will be started if necessary). """

    def __init__(self, server = None):
        super(ServerConnection, self).__init__()
        self._sock = (server or get_default_server()).connect()

    def issue_command(self, cmd, *args):
        """ Sends and receives a message to/from the server """
        self._writeline(cmd)
        self._writeline(str(len(args)))
        for arg in args:
            arg = str(arg)
            self._writeline(str(len(arg)))
            self._sock.send(arg)

        return self._read_response()

    def _read_response(self):
        """ Reads a complete response packet from the server """
        result = self._readline()
        if not result:
            raise NoResponseError, "No response received from server."

        if result != "ok":
            raise InvalidResponseError, self._read_message()

        return self._read_message()

    def _read_message(self):
        """ Reads a single size-annotated message from the server """
        size = int(self._readline())
        if size == 0:
            return ""
        else:
            return self._recvall(size)

    def _recvall(self, size):
        """ Receive until the given number of bytes is fetched or until EOF (in which
        case ``EndOfStreamError`` is raised). """
        result = []
        while size > 0:
            data = self._sock.recv(min(8192, size))
            if not data:
                raise EndOfStreamError, "Unexpected end of stream."
            result.append(data)
            size -= len(data)
        return ''.join(result)

    def _readline(self):
        """ Cheap implementation of a readline function that operates on our underlying
        socket. """
        res = []
        while True:
            c = self._sock.recv(1)
            if c == "\n":
                return "".join(res)
            res.append(c)

    def _writeline(self, line):
        """ Writes a line to the underlying socket. """
        self._sock.send(line + "\n")