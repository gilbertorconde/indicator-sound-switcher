import abc
import logging

from gi.repository import Gtk

from . import utils


class PreferencesDialog(Gtk.Dialog):
    """Indicator preferences dialog."""

    def __init__(self, indicator, parent: Gtk.Window=None):
        """Constructor.
        :param indicator: Sound Switcher Indicator instance
        :param parent: parent window
        """
        Gtk.Dialog.__init__(
            self, _('Sound Switcher Indicator Preferences'), parent, 0, (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))
        self.set_border_width(12)
        self.set_default_size(600, 400)
        self.indicator = indicator

        # Add notebook with pages
        notebook = MainNotebook(indicator)
        self.get_content_area().pack_start(notebook, True, True, 0)

        # Show all controls
        self.show_all()


class BasePage(Gtk.Box):
    """Base abstract class for notebook page objects."""

    def __init__(self, title: str, indicator):
        """Constructor."""
        super().__init__()
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(6)
        self.set_border_width(10)
        self.scroll_box = None
        self.is_initialised = False
        self.title = title
        self.indicator = indicator

    def get_label_widget(self):
        """Create and return a widget for the page label."""
        return Gtk.Label.new_with_mnemonic(self.title)

    def on_activate(self):
        """Is called whenever the page is activated."""
        if not self.is_initialised:
            # Call the page-specific initialisation
            self.initialise()
            self.is_initialised = True

    @abc.abstractmethod
    def initialise(self):
        """Must initialise the page."""


class GeneralPage(BasePage):
    """General page object."""

    def __init__(self, indicator):
        super().__init__(_('_General'), indicator)

        # Add inputs switch
        self.switch_inputs = Gtk.Switch()
        self.switch_inputs.connect('state-set', self.on_switch_inputs_set)
        self.pack_start(utils.labeled_widget(_('Show inputs'), self.switch_inputs, False), False, False, 0)

        # Add outputs switch
        self.switch_outputs = Gtk.Switch()
        self.switch_outputs.connect('state-set', self.on_switch_outputs_set)
        self.pack_start(utils.labeled_widget(_('Show outputs'), self.switch_outputs, False), False, False, 0)

    def initialise(self):
        self.switch_inputs.set_active (self.indicator.config['show_inputs',  True])
        self.switch_outputs.set_active(self.indicator.config['show_outputs', True])

        # Show all child widgets
        self.show_all()

    def on_switch_inputs_set(self, widget: Gtk.Switch, data):
        """Signal handler: Show Inputs switch set."""
        if not self.is_initialised:
            return
        logging.debug('.on_switch_inputs_set(%s)', widget.get_active())
        self.indicator.config['show_inputs'] = widget.get_active()
        self.indicator.on_refresh()

    def on_switch_outputs_set(self, widget: Gtk.Switch, data):
        """Signal handler: Show Outputs switch set."""
        if not self.is_initialised:
            return
        logging.debug('.on_switch_outputs_set(%s)', widget.get_active())
        self.indicator.config['show_outputs'] = widget.get_active()
        self.indicator.on_refresh()


class DevicesPage(BasePage):
    """Devices page object."""

    def __init__(self, indicator):
        super().__init__(_('_Devices'), indicator)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_spacing(6)

        # Add main grid
        grid = Gtk.Grid(border_width=12, column_spacing=6, row_spacing=6, hexpand=True, vexpand=True)
        self.pack_start(grid, True, True, 0)

        # Fill in the grid
        self._add_device_widgets(grid)
        self._add_device_props_widgets(grid)
        self._add_port_props_widgets(grid)

    def _add_device_widgets(self, grid: Gtk.Grid):
        """Add widgets for the device list to the main grid."""
        # Add a label
        grid.attach(utils.lbl_bold(_('Devices:')), 0, 0, 1, 1)

        # Add a scrollbox
        scrollbox = Gtk.ScrolledWindow(propagate_natural_width=True, min_content_height=300)
        scrollbox.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid.attach(scrollbox, 0, 1, 1, 1)

        # Add a list box with devices
        self.listbox_devices = Gtk.ListBox()
        self.listbox_devices.connect('row-selected', self.on_device_row_selected)
        scrollbox.add(self.listbox_devices)

    def _add_device_props_widgets(self, grid: Gtk.Grid):
        """Add widgets for device props to the main grid."""
        # Add a label
        grid.attach(utils.lbl_bold(_('Device settings:')), 1, 0, 1, 1)

        # Add a props wrapper box
        bx_wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True)
        grid.attach(bx_wrapper, 1, 1, 1, 1)

        # Add a placeholder label
        self.lbl_dev_props_placeholder = Gtk.Label(_('(select device first)'))
        bx_wrapper.pack_start(self.lbl_dev_props_placeholder, True, True, 0)

        # Add a props box
        self.box_dev_props = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6, border_width=12, hexpand=True, vexpand=True)
        bx_wrapper.pack_end(self.box_dev_props, True, True, 0)

        # Add a name label/entry
        self.entry_dev_name = Gtk.Entry(width_chars=20)
        self.box_dev_props.pack_start(utils.labeled_widget(_('Custom name:'), self.entry_dev_name), False, True, 0)

        # Add a label for port list box
        self.box_dev_props.pack_start(utils.lbl_bold(_('Ports:'), xalign=0),  False, True, 0)

        # Add a list box with ports
        self.listbox_ports = Gtk.ListBox()
        self.listbox_ports.connect('row-selected', self.on_port_row_selected)
        self.box_dev_props.pack_start(
            Gtk.ScrolledWindow(child=self.listbox_ports, vexpand=True), True, True, 0)

    def _add_port_props_widgets(self, grid: Gtk.Grid):
        """Add widgets for port props to the main grid."""
        # Add a label
        grid.attach(utils.lbl_bold(_('Port settings:')), 2, 0, 1, 1)

        # Add a props wrapper box
        bx_wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True)
        grid.attach(bx_wrapper, 2, 1, 1, 1)

        # Add a placeholder label
        self.lbl_port_props_placeholder = Gtk.Label(_('(select port first)'))
        bx_wrapper.pack_start(self.lbl_port_props_placeholder, True, True, 0)

        # Add a props box
        self.box_port_props = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6, border_width=12, hexpand=True, vexpand=True)
        bx_wrapper.pack_start(self.box_port_props, True, True, 0)

        # Add a visibility label/switch
        self.switch_port_visible = Gtk.Switch()
        # TODO add self.switch_port_visible.connect('state-set', ...)
        self.box_port_props.pack_start(
            utils.labeled_widget(_('Visible'), self.switch_port_visible, False), False, True, 0)

        # Add a name label/entry
        self.entry_port_name = Gtk.Entry(width_chars=20)
        self.box_port_props.pack_start(utils.labeled_widget(_('Custom name:'), self.entry_port_name), False, True, 0)

        # Add an always available label/switch
        self.switch_port_always_avail = Gtk.Switch()
        # TODO add self.switch_port_always_avail.connect('state-set', ...)
        self.box_port_props.pack_start(
            utils.labeled_widget(_('Always available'), self.switch_port_always_avail, False), False, True, 0)

        # Add a preferred profile label/dropdown
        self.cbox_port_pref_profile = Gtk.ComboBoxText()
        # TODO add self.cbox_port_pref_profile.connect('...', ...)
        self.box_port_props.pack_start(
            utils.labeled_widget(_('Preferred profile:'), self.cbox_port_pref_profile), False, True, 0)

    def initialise(self):
        for idx, card in self.indicator.cards.items():
            # Add a grid
            grid = Gtk.Grid(border_width=12, column_spacing=6, row_spacing=6, hexpand=True)

            # Add a list box row
            row = Gtk.ListBoxRow(child=grid)
            row.card = card

            # Add an icon
            grid.attach(Gtk.Image.new_from_icon_name('yast_soundcard', Gtk.IconSize.MENU), 0, 0, 1, 2)

            # Add a device title label
            grid.attach(utils.lbl_bold(card.get_display_name(), xalign=0), 1, 0,  1, 1)

            # Add a device name label
            grid.attach(Gtk.Label(card.name, xalign=0), 1, 1,  1, 1)

            # Add the grid as a list row
            self.listbox_devices.add(row)

        # Show all child widgets
        self.show_all()

        # Update device and port props widgets
        self.update_dev_props_widgets()
        self.update_port_props_widgets()

    def update_dev_props_widgets(self):
        """Update device props widgets."""
        # Get selected row
        row = self.listbox_devices.get_selected_row()

        # Remove all ports from the ports list box
        for port_row in self.listbox_ports.get_children():
            self.listbox_ports.remove(port_row)

        # If there's no selected row, hide the controls and show the placeholder
        if row is None:
            self.lbl_dev_props_placeholder.show()
            self.box_dev_props.hide()
        # Update widgets otherwise and hide the placeholder
        else:
            self.entry_dev_name.set_text(row.card.display_name)
            for name, port in row.card.ports.items():
                # Add a box for labels
                bx_port = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, border_width=6)
                bx_port.pack_start(utils.lbl_bold(port.get_display_name(), xalign=0), False, False, 0)
                bx_port.pack_start(Gtk.Label(port.name, xalign=0), False, False, 0)

                # Add a port row
                port_row = Gtk.ListBoxRow(child=bx_port)
                port_row.port = port
                self.listbox_ports.add(port_row)
            self.box_dev_props.show_all()
            self.lbl_dev_props_placeholder.hide()

    def update_port_props_widgets(self):
        """Update port props widgets."""
        # Get selected row
        row = self.listbox_ports.get_selected_row()

        # If there's no selected row, hide the controls and show the placeholder
        if row is None:
            self.lbl_port_props_placeholder.show()
            self.box_port_props.hide()
        # Update widgets otherwise and hide the placeholder
        else:
            self.entry_port_name.set_text(row.port.display_name)
            self.box_port_props.show_all()
            self.lbl_port_props_placeholder.hide()

    def on_device_row_selected(self, list_box: Gtk.ListBox, row: Gtk.ListBoxRow):
        """Signal handler: devices list box row (un)selected."""
        self.update_dev_props_widgets()

    def on_port_row_selected(self, list_box: Gtk.ListBox, row: Gtk.ListBoxRow):
        """Signal handler: ports list box row (un)selected."""
        self.update_port_props_widgets()


class MainNotebook(Gtk.Notebook):
    """Implementation of the preferences dialog's notebook control."""

    def __init__(self, indicator):
        logging.debug('Creating ' + self.__class__.__name__)
        super().__init__()

        # Create notebook pages
        self._add_page(GeneralPage(indicator))
        self._add_page(DevicesPage(indicator))

        # Connect page switch signal
        self.connect('switch-page', self.on_switch_page)

    def _add_page(self, page: BasePage):
        """Add a single (descendant of) BasePage."""
        self.append_page(page, page.get_label_widget())

    @staticmethod
    def on_switch_page(widget, page, index):
        """Signal handler: current page changed"""
        logging.debug('Page changed to %d', index)
        page.on_activate()
