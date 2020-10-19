"""Select helpers for notebooks."""

import functools
import sys

from colorama import Fore, Style
try:
    # we don't want the whole package to depend on these but for
    # functionality that is inherently notebookish these will
    # be present in that context
    from IPython import display
    import ipywidgets as widgets
except ImportError:
    pass


def cecho():
    """Print formatted text.

    Entrypoint to print formatted text:

        cecho error This message is printed in red

    Valid formats are: 'error', 'warning', 'ok', 'success'
    """
    style, *text = sys.argv[1:]
    text = ' '.join(text)
    if style == 'error':
        print(error(text))
    elif style == 'warning':
        print(warning(text))
    elif style == 'ok':
        print(ok(text))
    elif style == 'success':
        print(success(text))
    else:
        print(text)


def error(text):
    """Format text as heavy red."""
    return Fore.RED + Style.BRIGHT + text + Style.RESET_ALL


def warning(text):
    """Format text as heavy magenta."""
    return Fore.MAGENTA + Style.BRIGHT + text + Style.RESET_ALL


def ok(text):
    """Format text as heavy blue."""
    return Fore.BLUE + Style.BRIGHT + text + Style.RESET_ALL


def success(text):
    """Format text as heavy green."""
    return Fore.GREEN + Style.BRIGHT + text + Style.RESET_ALL


class InputSpec:
    """Create an item for an InputForm."""

    def __init__(
            self, key, description, widget_spec, long_desc=None,
            validator=None, err_msg=None):
        """Initialize an input form item.

        :param key: a unique key for the item. This is used within a
            `InputForm` to retrieve the value associated with the input.
        :param description: a short description of the input.
        :param widget_spec: anything that is accepted by
            `ipywidgets.interactive`, for clarity it may be best to give
            instances of widgets rather than abbreviations.
        :param long_desc: A long description of the value.
        :param validator: Callback to validate values, should accept a single
            argument and return True/False to indicate the value is valid.
        :param err_msg: Message associated with invalid values. The string may
            contain the formatting placeholders '{value}' and '{param}', which
            will be filled with the value and self.description.
        """
        self.key = key
        self.description = description
        self.widget_spec = widget_spec
        self.long_desc = long_desc
        self.validator = validator
        if self.validator is None:
            self.validator = lambda x: True
        self.err_msg = err_msg
        if self.err_msg is None:
            self.err_msg = "Invalid value '{value}' for '{param}' parameter."

    def valid_value(self, value):
        """Return whether a given value passes validation.

        :param value: value to validate.

        :returns: (True/False, error string or None)
        """
        valid, msg = True, None
        if not self.validator(value):
            valid = False
            msg = self.err_msg.format(value=value, param=self.description)
        return valid, msg


class InputForm:
    """Easily create an input form in a notebook and store values."""

    def __init__(self, *args, widget_width='400px', description_width='150px'):
        """Initialize a form.

        :param args: args should be each an `InputSpec`.

        The current value of an item can be accessed as an attribute of the
        class using the key. The short description is displayed alongside the
        input form item, while the long description is displayed above the
        item.

        >>> inputs = InputForm(
        >>>     InputSpec(
        >>>         'a', 'My a value',
        >>>         {'min':-10, 'max':30, 'step':1, 'value':1},
        >>>         validator=lambda x: x==1,
        >>>         err_msg="Value must be equal to one."),
        >>>     InputSpec(
        >>>         'input_file', 'Input Bam', 'sample/data/mybam.bam',
        >>>         long_desc='Your input bam file should be a bam file',
        >>>         validator=lambda x: os.path.isfile(x),
        >>>         err_msg="'{value}' is not an existing file '{param}'"),
        >>>     InputSpec(
        >>>         'b', 'My b value',
        >>>         widgets.IntSlider(value=-3, max=30, min=-10)))
        >>> inputs.display()
        """
        self.widgets = dict()   # value holding widgets
        self._widgets = dict()  # for display
        self.options = args
        for option in self.options:
            if option.long_desc is not None:
                self._widgets['{}_desc'.format(option.key)] = \
                    widgets.HTML(option.long_desc)
            setter = functools.partial(self._set_value, self)
            setter.__name__ = 'setter_{}'.format(option.key)
            # create interactive widget, saves writing callback,
            # .result on the object gives the current value
            spec = {'value': option.widget_spec}
            widget = widgets.interactive(setter, **spec)
            # grab the useful part of the above and manipulate for consistency
            wid = widget.children[0]
            wid.description = ''
            wid.style.description_width = '0px'
            wid.layout = widgets.Layout(width=widget_width)
            # add label in a consistent manner
            self._widgets[option.key] = widgets.HBox([
                widgets.Label(
                    option.description,
                    layout=widgets.Layout(width=description_width)),
                widget])
            self.widgets[option.key] = widget

    def add_process_button(self, callback):
        """Add a button to do something with current values.

        :param callback: a function, should accept this class
            as a single argument. The intention here is the callback
            can mutate the class to add additional attributes after
            performing some work.
        """
        self._widgets['enter_button'] = widgets.Button(
            description='Enter', icon='angle-right')
        self._widgets['process_output'] = widgets.Output()

        def set_button_idle():
            self._widgets['enter_button'].description = 'Enter'
            self._widgets['enter_button'].disabled = False
            self._widgets['enter_button'].icon = 'angle-right'

        def set_button_busy():
            self._widgets['enter_button'].description = 'Processing'
            self._widgets['enter_button'].disabled = True
            self._widgets['enter_button'].icon = 'fa-spinner'

        def on_butt_clicked(b):
            set_button_busy()
            with self._widgets['process_output']:
                display.clear_output()
                callback(self)
                set_button_idle()

        self._widgets['enter_button'].on_click(on_butt_clicked)

    def display(self):
        """Display the input form."""
        display.display(widgets.VBox([*self._widgets.values()]))

    def validate(self):
        """Validate inputs.

        :returns: a tuple: (True/False, list of error messages)
        """
        valid = True
        errors = list()
        for desc, value, opt_valid, err_msg in self:
            if not opt_valid:
                valid = False
                errors.append(err_msg)
        return valid, errors

    def report(self, colour=False):
        """Create a report of values and errors.

        :param colour: colourize error and success text.
        """
        results = list()
        all_valid = True
        for desc, value, valid, err_msg in self:
            results.append('{}: {}'.format(desc, value))
            if not valid:
                all_valid = False
                msg = " - {}".format(err_msg)
                if colour:
                    msg = error(msg)
                results.append(msg)
        if all_valid:
            msg = "All inputs passed validation."
            if colour:
                msg = success(msg)
        else:
            msg = "One or more values failed validation."
            if colour:
                msg = error(msg)
        results.append(msg)
        return '\n'.join(results)

    def __getattr__(self, key):
        """Fetch the value of a widget item, or just a plain attribute."""
        if key in self.widgets:
            attr = self.widgets[key].result
        else:
            try:
                attr = getattr(super(), key)
            except AttributeError:
                raise AttributeError(
                    '{} instance has no attribute {}'.format(type(self), key))
        return attr

    def __iter__(self):
        """Iterate over option values.

        :yields: description, value, is valid?, error message
        """
        for option in self.options:
            value = getattr(self, option.key)
            valid, err_msg = option.valid_value(value)
            yield option.description, value, valid, err_msg

    @staticmethod
    def _set_value(self, value):
        return value
