import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import ipywidgets as widgets
from ipywidgets import Layout
import obspy
import warnings
from datetime import datetime
import ucla_geotech_tools.response_spectrum as ars
from obspy.geodetics import gps2dist_azimuth
from gmprocess.io.asdf.stream_workspace import StreamWorkspace


class HumanReviewGUI:
    """The HumanReviewGUI class creates the graphical user interface (GUI)
    used for reviewing ground motion data processed by gmprocess.

    Attributes (in alphabetical order)
    ----------
        acc_u (array):
            Numpy array containing unprocessed acceleration time series

        accept_button (obj):
            ipywidgets object for "Accept" button

        accepted_widget (obj):
            ipywidgets object for "Accepted" checkbox. Selecting this box shows the reviewed traces that were accepted.

        ax (array of obj):
            array of matplotlib axis objects

        Cha (str):
            Channel name (e.g., BHE)

        dt (float)
            acceleration time series' time step

        event_id (int):
            Unique identifier for earthquake event

        fchp_widget (obj):
            ipywidgets object for high-pass corner frequency. Here you can increase or decrease the fchp chosen by gmprocess.

        fclp_checkbox_widget (obj):
            ipywidgets object for checkbox to enable low-pass filter

        fclp_display (float)

        fclp_widget (obj):
            ipywidgets object for low-pass corner frequency. Here you can increase or decrease the fclp chosen by gmprocess.

        fig (obj):
            matplotlib figure object

        freq_u (array):
            Numpy array containing frequency vector for unprocessed Fourier spectra

        human_review (dict):
            Python dictionary for storing review parameters

        ln (array of obj):
            array of matplotlib line objects for data plots

        ln_filt (array of obj):
            array of matplotlib line objects for filter parameter plots

        load_workspace_button (obj):
            ipywidgets object for "Load" button (loads workspace.h5)

        metadata_widget (obj):
            ipywidgets object containing metadata (e.g., user, magnitude, distance)

        NCR (str):
            Network, channel, record identifier (e.g., IM.TX31..BHE_usc000nz6j_default)

        NetSta (str):
            Network and station fields concatenated. Period separated (e.g., IM.TX31)

        next_button (obj):
            ipywidgets object for "Next" button. Clicking this button moves to the next trace.

        NFFT (int):
            Number of points in Fourier transform

        not_reviewed_widget (obj):
            ipywidgets object for "Not Reviewed" checkbox. Selecting this box shows the unreviewed traces

        output_widget (obj):
            ipywidgets object for output field containing status messages

        previous_button (obj):
            ipywidgets object for "Previous" button. Clicking this button moves to the previous trace.

        reject_button (obj):
            ipywidgets object for "Reject" button. Clicking this button rejects the trace.

        rejected_widget (obj):
            ipywidgets object for "Rejected" checkbox. Selecting this box shows the reviewed tracess that were rejected.

        T (array):
            Natural periods for pseudo acceleration response spectrum

        tr (obj):
            Obspy trace for acceleration time series processed by gmprocess

        trace_data (obj):
            ObsPy object containing selected trace

        version_widget (obj):
            ipywidgets object for gmprocess version dropdown menu. Select 1.2.0 for any versions prior to 1.2.9.

        waveform_widget (obj):
            ipywidgets object for waveform dropdown menu

        workspace (obj):
            StreamWorkspace object for gmprocess workspace

        workspace_widget (obj):
            ipywidgets object for the name of the workspace.h5 file
    """

    def __init__(self):
        """
        Initialize the GUI.
        """
        self.human_review = {}
        self.acc_u = None
        self.Cha = None
        self.dt = None
        self.event_id = None
        self.freq_u = None
        self.NCR = None
        self.NetSta = None
        self.NFFT = None
        self.T = None
        self.tr = None
        self.trace_data = None
        self.workspace = None

        style = {"description_width": "initial"}
        self.workspace_widget = widgets.Text(value="workspace.h5", disabled=False)
        self.load_workspace_button = widgets.Button(
            description="Load", button_style="", disabled=False
        )

        self.not_reviewed_widget = widgets.Checkbox(
            value=True,
            description="Not Reviewed",
            indent=False,
            layout=widgets.Layout(width="120px"),
        )
        self.accepted_widget = widgets.Checkbox(
            value=False,
            description="Accepted",
            indent=False,
            layout=widgets.Layout(width="120px"),
        )
        self.rejected_widget = widgets.Checkbox(
            value=False,
            description="Rejected",
            indent=False,
            layout=widgets.Layout(width="120px"),
        )
        self.previous_button = widgets.Button(
            description="<< previous", button_style="info", disabled=True
        )
        self.waveform_widget = widgets.Dropdown(options=[], disabled=True)
        self.next_button = widgets.Button(
            description="next >>", button_style="info", disabled=True
        )
        self.accept_button = widgets.Button(
            description="accept >>", button_style="success", disabled=True
        )
        self.reject_button = widgets.Button(
            description="reject >>", button_style="danger", disabled=True
        )
        self.metadata_widget = widgets.HTML(layout=Layout(width="55%"))
        self.fchp_widget = widgets.FloatText(
            description="fchp (Hz):",
            indent=False,
            disabled=True,
            step=0.01,
            min=0.0,
            layout=Layout(width="17%"),
        )
        self.fclp_checkbox_widget = widgets.Checkbox(
            value=True, description="fclp", indent=False
        )
        self.fclp_widget = widgets.FloatText(
            description="fclp (Hz):",
            indent=False,
            disabled=True,
            step=1.0,
            min=1.0,
            value=100,
            layout=Layout(width="15%"),
        )
        self.progress_widget = widgets.IntProgress(description='Loading:',bar_style='info', 
            orientation='horizontal',layout=Layout(width="80%")) 

        panel = widgets.VBox(
            [
                self.progress_widget,
                widgets.HBox(
                    [
                        self.workspace_widget,
                        self.load_workspace_button,
                        self.not_reviewed_widget,
                        self.accepted_widget,
                        self.rejected_widget,
                    ]
                ),
                widgets.HBox(
                    [
                        self.previous_button,
                        self.waveform_widget,
                        self.next_button,
                        self.accept_button,
                        self.reject_button,
                    ]
                ),
                widgets.HBox(
                    [
                        self.metadata_widget,
                        self.fchp_widget,
                        self.fclp_widget,
                        self.fclp_checkbox_widget,
                    ],
                    justify_content="flex-start",
                ),
            ]
        )
        self.set_waveform_list({})
        self.previous_button.disabled = True
        self.next_button.disabled = False
        self.accept_button.disabled = False
        self.reject_button.disabled = False
        self.fchp_widget.disabled = False
        self.fclp_widget.disabled = False
        display(panel)
        self.fig, self.ax = plt.subplots(nrows=2, ncols=2, figsize=(8, 6), dpi=100)
        self.ax[0, 0].set_ylabel("acc (m/s$^2$)")
        self.ax[0, 0].set_xlabel("time (s)")
        self.ax[1, 0].set_ylabel("disp (m)")
        self.ax[1, 0].set_xlabel("time (s)")
        self.ax[0, 1].set_ylabel("|Facc| (m/s)")
        self.ax[0, 1].set_xlabel("freq (Hz)")
        self.ax[0, 1].set_xlim(0.001, 100.0)
        self.ax[1, 1].set_ylabel("Sa (g)")
        self.ax[1, 1].set_xlabel("period (s)")
        self.ax[1, 1].set_xlim(0.01, 20.0)
        self.ln = {}
        self.ln_filt = {}
        (self.ln["acc_u"],) = self.ax[0, 0].plot([], [], c="C1", zorder=1)
        (self.ln["acc_filt"],) = self.ax[0, 0].plot([], [], c="C0", zorder=2)
        (self.ln["acc"],) = self.ax[0, 0].plot([], [], alpha=0.5, c="C3", zorder=3)
        (self.ln["disp_filt"],) = self.ax[1, 0].plot([], [], c="C0", zorder=2)
        (self.ln["disp"],) = self.ax[1, 0].plot([], [], alpha=0.5, c="C3", zorder=3)
        (self.ln["Facc_u"],) = self.ax[0, 1].plot(
            [0.01], [0.01], label="unfiltered", c="C1", zorder=1
        )
        (self.ln["Facc"],) = self.ax[0, 1].plot(
            [0.01], [0.01], alpha=0.5, c="C3", label="filtered gmprocess", zorder=4
        )
        (self.ln["Facc_filt"],) = self.ax[0, 1].plot(
            [0.01], [0.01], label="filtered GUI", c="C0", zorder=3
        )
        (self.ln["smooth_noise_spectrum"],) = self.ax[0, 1].plot(
            [], [], c="C2", label="noise", zorder=2
        )
        (self.ln["snr"],) = self.ax[0, 1].plot(
            [], [], c="gray", label="SNR", zorder=2
        ) 
        self.flag_plot = 0 #flag_plot will help to create the legend only once
        self.ln_filt["Facc_fchp"] = self.ax[0, 1].axvline(
            x=0.01, label="f$_c$", linestyle="--", color="black"
        )
        self.ln_filt["Facc_fclp"] = self.ax[0, 1].axvline(
            x=0.01, linestyle="--", color="black"
        )
        (self.ln["f2_line"],) = self.ax[0, 1].plot(
            [], [], label="f$^2$ model", c="black", linestyle=":"
        )
        (self.ln["Sa_u"],) = self.ax[1, 1].plot([0.01], [0.01], c="C1", zorder=1)
        (self.ln["Sa"],) = self.ax[1, 1].plot(
            [0.01], [0.01], alpha=0.5, c="C3", zorder=3
        )
        (self.ln["Sa_filt"],) = self.ax[1, 1].plot([0.01], [0.01], c="C0", zorder=2)
        self.ln_filt["Tmax"] = self.ax[1, 1].axvline(
            x=0.01, linestyle="--", color="black"
        )
        # self.ln_filt["Tmin"] = self.ax[1, 1].axvline(x=0.01, linestyle="--", color="black") #Sometimes the user wants to see where the fclp influences in the PSA
        self.ax[0, 1].set_xscale("log")
        self.ax[1, 1].set_xscale("log")
        self.ax[0, 1].set_yscale("log")
        self.ax[1, 1].set_yscale("log")
        for a1 in self.ax:
            for a in a1:
                # a.autoscale_view()
                a.grid(True, alpha=0.5, which="both")
        plt.tight_layout()
        self.next_button.on_click(self.next_waveform)
        self.previous_button.on_click(self.previous_waveform)
        self.waveform_widget.observe(self.waveform_widget_change, names=["value"])
        self.fchp_widget.observe(self.fc_change, names=["value"])
        self.fclp_widget.observe(self.fc_change, names=["value"])
        self.fclp_checkbox_widget.observe(self.fc_change, names=["value"])
        self.accept_button.on_click(self.accept_record)
        self.reject_button.on_click(self.reject_record)
        self.not_reviewed_widget.observe(self.set_waveform_list, names=["value"])
        self.accepted_widget.observe(self.set_waveform_list, names=["value"])
        self.rejected_widget.observe(self.set_waveform_list, names=["value"])
        self.load_workspace_button.on_click(self.load_workspace)

    def load_workspace(self, b):
        """
        Loads gmprocess HDF5 file specified in workspace_widget text field.
        Args:
            b: Dummy variable needed to run Jupyter Widgets.
        """
        self.load_workspace_button.disabled = True
        self.workspace = StreamWorkspace.open(self.workspace_widget.value)
        self.progress_widget.max = len(self.workspace.dataset.waveforms.list())
        try:
            self.event_id = self.workspace.getEventIds()[0]
        except:
            self.event_id = self.workspace.get_event_ids()[0]
        self.trace_data = pd.DataFrame()
        NetSta_array = []
        Channel_array = []
        Streams_index_array = []
        Trace_index_array = []
        Distance_array = []
        lat_event = self.workspace.dataset.events.events[0].origins[0].latitude
        long_event = self.workspace.dataset.events.events[0].origins[0].longitude
        self.reviewed_count = 0
        for NetSta in self.workspace.dataset.waveforms.list():
            try:
                streams = self.workspace.getStreams(
                    self.event_id, stations=[NetSta], labels=["default"]
                )
            except:
                streams = self.workspace.get_streams(
                    self.event_id, stations=[NetSta], labels=["default"]
                )
            for i in range(0, len(streams)):
                stream = streams[i]
                if stream.passed:
                    for j, tr in enumerate(stream):
                        cha = tr.meta.channel
                        try:
                            try:
                                accepted = tr.getParameter("review")["accepted"]
                            except:
                                accepted = tr.get_parameter("review")["accepted"]
                            if accepted:
                                self.human_review[NetSta + ", " + cha] = {
                                    "reviewed": 1,
                                    "accepted": 1,
                                }
                            else:
                                self.human_review[NetSta + ", " + cha] = {
                                    "reviewed": 1,
                                    "accepted": 0,
                                }
                            self.reviewed_count += 1
                        except:
                            self.human_review[NetSta + ", " + cha] = {
                                "reviewed": 0,
                                "accepted": 0,
                            }
                        try:
                            lat_sta = streams[i].getInventory()[0][0].latitude
                            long_sta = streams[i].getInventory()[0][0].longitude
                        except:
                            lat_sta = streams[i].get_inventory()[0][0].latitude
                            long_sta = streams[i].get_inventory()[0][0].longitude
                        distance = np.round(
                            (
                                gps2dist_azimuth(
                                    lat_sta, long_sta, lat_event, long_event
                                )[0]
                                / 1000.0
                            ),
                            2,
                        )
                        NetSta_array.append(NetSta)
                        Channel_array.append(cha)
                        Streams_index_array.append(i)
                        Trace_index_array.append(j)
                        Distance_array.append(distance)
            self.progress_widget.value += 1
            
        self.trace_data["NetSta"] = NetSta_array
        self.trace_data["Channel"] = Channel_array
        self.trace_data["Streams_index"] = Streams_index_array
        self.trace_data["Trace_index"] = Trace_index_array
        self.trace_data["Repi"] = Distance_array
        self.load_workspace_button.disabled = False
        
        self.total_count = len(NetSta_array)
        self.progress_widget.description="%s%s%s%s%s" % ("Progress (",self.reviewed_count,"/",self.total_count,"):") 
        self.progress_widget.style= {'description_width': 'initial'}
        self.progress_widget.max = self.total_count 
        self.progress_widget.value = self.reviewed_count 
        
        self.set_waveform_list({})
        return

    def set_waveform_list(self, change):
        """
        Sets list of waveforms in waveform_widget dropdown.
        Args:
            change: Dummy variable needed to run Jupyter Widgets.
        """
        selection = self.waveform_widget.value
        waveform_options = []
        for key, value in self.human_review.items():
            if (value["reviewed"] == 0) and (self.not_reviewed_widget.value == True):
                waveform_options.append(key)
            if (value["accepted"] == 1) and (self.accepted_widget.value == True):
                waveform_options.append(key)
            if (value["accepted"] == 0) and (self.rejected_widget.value == True):
                waveform_options.append(key)
        self.waveform_widget.disabled = False
        self.waveform_widget.options = waveform_options
        if selection in waveform_options:
            self.waveform_widget.value = selection
        return

    def waveform_widget_change(self, change):
        """
        Updates plots on change in waveform_widget dropdown.
        Args:
            change: Dummy variable needed to run Jupyter Widgets.
        """
        if self.waveform_widget.value == None:
            return
        if change["new"] == False:
            return
        I = self.waveform_widget.options.index(self.waveform_widget.value)
        self.previous_button.disabled = False
        self.next_button.disabled = False
        if I == 0:
            self.previous_button.disabled = True
        if I == len(self.waveform_widget.options) - 1:
            self.next_button.disabled = False
        self.update_plots()
        return

    def update_plots(self):
        """
        Updates plots by modifying ln and ln_filt objects.
        """
        self.NetSta = self.waveform_widget.value.split(", ")[0]
        self.Cha = self.waveform_widget.value.split(", ")[1]
        self.trace_row = self.trace_data[
            (self.trace_data["NetSta"] == self.NetSta)
            & (self.trace_data["Channel"] == self.Cha)
        ]
        if len(self.trace_row) > 1:
            print("There is more than one record with the same NetSta and Channel!")
            return

        try:
            streams = self.workspace.getStreams(
                self.event_id, stations=[self.NetSta], labels=["default"]
            )
            streams_u = self.workspace.getStreams(
                self.event_id, stations=[self.NetSta], labels=["unprocessed"]
            )
        except:
            streams = self.workspace.get_streams(
                self.event_id, stations=[self.NetSta], labels=["default"]
            )
            streams_u = self.workspace.get_streams(
                self.event_id, stations=[self.NetSta], labels=["unprocessed"]
            )
        i = self.trace_row["Streams_index"].values[0]
        j = self.trace_row["Trace_index"].values[0]
        self.tr = streams[i][j]
        self.NCR = self.tr.id + "_" + self.event_id + "_default"
        tr_u = streams_u[i][j]
        tr_u.data = tr_u.data - np.mean(tr_u.data)
        self.dt = self.tr.stats.delta
        npts = self.tr.stats.npts
        nt = min(self.tr.stats.starttime - tr_u.stats.starttime, 60)
        time = np.linspace(self.dt + nt, (self.dt * npts) + nt, npts)
        try:
            rr_units = self.tr.getProvenance("remove_response")[0]['output_units']
        except:
            rr_units = self.tr.get_provenance("remove_response")[0]['prov_attributes']['output_units']
        if "cm/s^2" in rr_units:
            Output = "ACC"
        else:
            Output = "VEL"
        station_metrics = self.workspace.dataset.waveforms[self.NetSta].StationXML
        try:
            WaterLevel = self.tr.getProvenance("remove_response")[0]['water_level']
            PreFilt = self.tr.getProvenance("remove_response")[0]['pre_filt_freqs']
            desired_array = np.fromstring(PreFilt[1:-1], sep=',')
            with warnings.catch_warnings(record=True):
                tr_u.remove_response(
                    inventory=station_metrics,
                    output=Output,
                    water_level=WaterLevel,
                    pre_filt=(
                        desired_array[0],
                        desired_array[1],
                        desired_array[2],
                        desired_array[3],
                    ),
                )
        except:
            try:
                WaterLevel = self.tr.get_provenance("remove_response")[0]['prov_attributes']['water_level']
                PreFilt = self.tr.get_provenance("remove_response")[0]['prov_attributes']['pre_filt_freqs']
                desired_array = np.fromstring(PreFilt[1:-1], sep=',')
                
                with warnings.catch_warnings(record=True):
                    tr_u.remove_response(
                        inventory=station_metrics,
                        output=Output,
                        water_level=WaterLevel,
                        pre_filt=(
                            desired_array[0],
                            desired_array[1],
                            desired_array[2],
                            desired_array[3],
                        ),
                    )
            except:
                try:
                    with warnings.catch_warnings(record=True):
                        tr_u.remove_response(inventory=station_metrics, output=Output)
                except:
                    tr_u.data = tr_u.data / 100
        tr_u.trim(self.tr.stats.starttime - nt, self.tr.stats.endtime)
        tr_u.taper(type="hann", max_percentage=0.05, side="both")
        tr_u.data = tr_u.data - np.mean(tr_u.data)
        tr_u_plot = tr_u.copy()
        npts_u = len(tr_u.data)
        acc = self.tr.data / 100.0
        acc = acc - np.mean(acc)
        if "cm/s^2" in rr_units:
            self.acc_u = tr_u.data
            acc_u_plot = tr_u_plot.data
        else:
            self.acc_u = tr_u.differentiate(frequency=True)
            self.acc_u = self.acc_u.data
            acc_u_plot = tr_u_plot.differentiate(frequency=True)
            acc_u_plot = acc_u_plot.data
        time_u = np.linspace(self.dt, self.dt * len(acc_u_plot), len(acc_u_plot))
        self.T = ars.get_ngawest2_T()
        Sa = ars.get_response_spectrum(
            motions=[acc/9.81], T=self.T, D=0.05, dt=self.dt, verbose=0, zeropad=0
        )
        Sa_u = ars.get_response_spectrum(
            motions=[acc_u_plot/9.81], T=self.T, D=0.05, dt=self.dt, verbose=0, zeropad=0
        )
        self.NFFT = npts_u
        Facc = np.fft.rfft(acc, n=npts)
        freq = np.fft.rfftfreq(npts, d=self.dt)
        Facc_u = np.fft.rfft(acc_u_plot, n=self.NFFT)
        self.freq_u = np.fft.rfftfreq(self.NFFT, d=self.dt)
        Fdisp = Facc[freq > 0] / -((2 * np.pi * freq[freq > 0]) ** 2)
        Fdisp = np.hstack((0.0, Fdisp))
        disp = np.fft.irfft(Fdisp, n=npts)[0 : len(acc)]
        try:
            try:
                fchp = self.tr.getParameter("review")["corner_frequencies"]["highpass"]
            except:
                fchp = self.tr.get_parameter("review")["corner_frequencies"]["highpass"]
            review_flag = 1 #indicator that the record has been reviewed. It's used to check on uncheck fclp_checkbox_widget
        except:
            
            try:
                fchp = self.tr.getParameter("corner_frequencies")['highpass']
            except:
                fchp = self.tr.get_parameter("corner_frequencies")['highpass']
            fchp = np.round(fchp, 4)
            review_flag = 0 #indicator that the record has been reviewed. It's used to check on uncheck fclp_checkbox_widget
        try:
            try:
                self.fclp_display = self.tr.getParameter("review")[
                    "corner_frequencies"
                ]["lowpass"]
            except:
                self.fclp_display = self.tr.get_parameter("review")[
                    "corner_frequencies"
                ]["lowpass"]
            self.fclp_checkbox_widget.value = True 
        except:
            if review_flag == 1:
                self.fclp_checkbox_widget.value = False #if the record was reviewed and the previous "try" couldn't find "lowpass" means that the record doesn't need to filter out the high frequencies.
            else:
                self.fclp_checkbox_widget.value = True #if the record was not reviewed, then show the fclp.
            try:
                self.fclp_display = self.tr.getParameter("corner_frequencies")['lowpass']
            except:
                self.fclp_display = self.tr.get_parameter("corner_frequencies")['lowpass']
        FAS_f2 = np.abs(Facc[freq > 0]) / (freq[freq > 0]) ** 2
        f2_amp = np.mean(FAS_f2[FAS_f2 > 0.5 * np.max(FAS_f2)])
        f_plot = np.asarray([0.003, 10.0])
        FAS_plot = f2_amp * f_plot**2 * self.dt / np.sqrt(len(Facc))
        noise_freq = np.asarray(self.tr.cached["noise_spectrum"]["freq"])
        smooth_noise_freq = np.asarray(self.tr.cached["smooth_noise_spectrum"]["freq"])
        smooth_noise_spec = np.asarray(self.tr.cached["smooth_noise_spectrum"]["spec"])
        snr_freq = np.asarray(self.tr.cached["snr"]["freq"]) 
        snr_spec = np.asarray(self.tr.cached["snr"]["snr"]) 
        
        if self.flag_plot == 0: #flag_plot will help to create the legend only once
            threshold = self.tr.getParameter("snr_conf")['threshold']
            (self.ln["snr_3"],) = self.ax[0, 1].plot([0.003, 100.0],[threshold*min(FAS_plot), threshold*min(FAS_plot)],linestyle="--", c="gray", zorder=2, label=f"SNR={threshold}")
            handles, labels = self.ax[0,1].get_legend_handles_labels()
            order = [0,1,2,3,4,7,5,6]
            self.ax[0, 1].legend([handles[k] for k in order], [labels[k] for k in order], ncol=2, prop={"size": 8})
            self.flag_plot = 1
        
        self.ln["acc_u"].set_data(time_u, acc_u_plot)
        self.ln["acc"].set_data(time, acc)
        self.ln["disp"].set_data(time, disp)
        self.ln["Facc"].set_data(
            freq[freq > 0], np.abs(Facc[freq > 0] * self.dt / np.sqrt(len(Facc)))
        )
        self.ln["smooth_noise_spectrum"].set_data(
            smooth_noise_freq[(smooth_noise_freq > 0) & (smooth_noise_spec > 0)],
            smooth_noise_spec[(smooth_noise_freq > 0) & (smooth_noise_spec > 0)]
            / 100
            / np.sqrt(len(noise_freq)),
        )
        self.ln["snr"].set_data(snr_freq,snr_spec * min(FAS_plot)) 
        self.ln["Sa"].set_data(self.T, Sa[0])
        self.ln["Sa_u"].set_data(self.T, Sa_u[0])
        self.ln["Facc_u"].set_data(
            self.freq_u[self.freq_u > 0],
            np.abs(Facc_u[self.freq_u > 0] * self.dt / np.sqrt(len(Facc_u))),
        )
        self.ln["f2_line"].set_data(f_plot, FAS_plot)
        fchp_old = self.fchp_widget.value
        fclp_old = np.round(self.fclp_display, 1)
        self.fchp_widget.value = fchp  # this makes fc_change run
        self.fclp_widget.value = np.round(
            self.fclp_display, 1
        )  # this makes fc_change run
        if (self.fchp_widget.value == fchp_old) and (
            self.fclp_widget.value == fclp_old
        ):
            self.fc_change(" ")
        metadata_html = (
            "User: "
            + self.workspace.config["user"]["name"]
            + ";   Magnitude: "
            + str(self.workspace.dataset.events.events[0].magnitudes[0].mag)
            + ";   Epicentral Dist.: "
            + str(self.trace_row["Repi"].values[0])
            + " km"
        )
        self.metadata_widget.value = metadata_html
        self.ax[0, 0].set_xlim(0, max(time))
        self.ax[1, 0].set_xlim(0, max(time))
        self.fig.tight_layout()
        return

    def fc_change(self, change):
        """
        Filters unprocessed data upon change in filter widgets, and plots filtered data.
        Args:
            change: Dummy variable needed to run Jupyter Widgets.
        """
        if self.fclp_checkbox_widget.value == True:
            fclp_corner = self.fclp_widget.value
            # self.ln_filt["Tmin"].set_xdata(x=1.25 / fclp_corner) #Sometimes the user wants to see where the fclp influences in the PSA
        else:
            fclp_corner = None
            # self.ln_filt["Tmin"].set_xdata(x=None) #Sometimes the user wants to see where the fclp influences in the PSA
        acc_filt = self.apply_filter()
        acc_filt = acc_filt - np.mean(acc_filt)
        time = np.linspace(0, len(acc_filt) * self.dt, len(acc_filt))
        Facc_filt = np.fft.rfft(acc_filt)
        Fdisp_filt = Facc_filt[self.freq_u > 0] / -(
            (2 * np.pi * self.freq_u[self.freq_u > 0]) ** 2
        )
        Fdisp_filt = np.hstack((0.0, Fdisp_filt))
        disp_filt = np.fft.irfft(Fdisp_filt)
        Sa_filt = ars.get_response_spectrum(
            motions=[acc_filt/9.81], T=self.T, D=0.05, dt=self.dt, verbose=0, zeropad=0
        )
        self.ln["Facc_filt"].set_data(
            self.freq_u[self.freq_u > 0],
            np.abs(Facc_filt[self.freq_u > 0] * self.dt / np.sqrt(len(Facc_filt))),
        )
        self.ln["Sa_filt"].set_data(self.T, Sa_filt[0])
        self.ln["acc_filt"].set_data(time, acc_filt)
        self.ln["disp_filt"].set_data(time, disp_filt)
        self.ln_filt["Facc_fchp"].set_xdata(x=self.fchp_widget.value)
        self.ln_filt["Facc_fclp"].set_xdata(x=fclp_corner)
        self.ln_filt["Tmax"].set_xdata(x=1 / (1.25 * self.fchp_widget.value))
        
        for a1 in self.ax:
            for a in a1:
                a.relim()
                a.autoscale_view()
                a.grid(True, alpha=0.5)

    def apply_filter(self):
        """
        Called by fc_change, and applies specified filter.
        Return:
            Filtered acceleration array.      
        """
        fchp_corner = self.fchp_widget.value
        if self.fclp_checkbox_widget.value == True:
            fclp_corner = self.fclp_widget.value
        else:
            fclp_corner = None
        try:
            number_of_passes = self.tr.getProvenance("highpass_filter")[0]['number_of_passes']
            filter_order = self.tr.getProvenance("highpass_filter")[0]['filter_order']
        except:
            number_of_passes = self.tr.get_provenance("highpass_filter")[0]['prov_attributes']['number_of_passes']
            filter_order = self.tr.get_provenance("highpass_filter")[0]['prov_attributes']['filter_order']
        filter_type = "Butterworth"
        if filter_type == "Butterworth ObsPy":
            tr_acc_filt = obspy.Trace(self.acc_u, header={"dt": self.dt})
            for i in range(int(np.round(number_of_passes / 2))):
                tr_acc_filt.filter(
                    "bandpass",
                    freqmin=fchp_corner * self.dt,
                    freqmax=fclp_corner * self.dt,
                    corners=filter_order,
                    zerophase=True,
                )
            return tr_acc_filt.data
        elif filter_type == "Butterworth":
            Facc = np.fft.rfft(self.acc_u)
            freq = np.fft.rfftfreq(n=self.NFFT, d=self.dt)
            Facc[freq == 0.0] = 0
            Facc[freq > 0.0] = Facc[freq > 0.0] / (
                np.sqrt(1 + (fchp_corner / freq[freq > 0.0]) ** (2 * filter_order))
            )
            if fclp_corner is not None:
                Facc[freq > 0.0] = Facc[freq > 0.0] / (
                    np.sqrt(1 + (freq[freq > 0.0] / fclp_corner) ** (2 * filter_order))
                )
            return np.fft.irfft(Facc)[0 : len(self.acc_u)]
        else:
            return "Incorrect filter type"

    def next_waveform(self, b):
        """
        Loads next waveform in list upon press of next_button.
        Args:
            b: Dummy variable needed to run Jupyter Widgets.
        """
        I = self.waveform_widget.options.index(self.waveform_widget.value)
        if I == len(self.waveform_widget.options) - 2:
            self.next_button.disabled = True
        self.waveform_widget.value = self.waveform_widget.options[I + 1]
        self.previous_button.disabled = False
        return

    def previous_waveform(self, b):
        """
        Loads previous waveform in list upon press of previous_button.
        Args:
            b: Dummy variable needed to run Jupyter Widgets.
        """
        I = self.waveform_widget.options.index(self.waveform_widget.value)
        if I == 1:
            self.previous_button.disabled = True
        self.waveform_widget.value = self.waveform_widget.options[I - 1]
        self.next_button.disabled = False
        return

    def accept_record(self, b):
        """
        Updates human_review instance variable in auxiliary_data upon press of accept_button.
        Args:
            b: Dummy variable needed to run Jupyter Widgets.
        """
        self.clear_plots()
        try:  # Delete auxiliary_data for record if it exists
            del self.workspace.dataset.auxiliary_data.review[self.NetSta][self.NCR]
        except:
            pass
        path = self.NetSta + "/" + self.NCR + "/"
        data = np.asarray([self.fchp_widget.value])
        self.workspace.dataset.add_auxiliary_data(
            data=data,
            data_type="review",
            path=path + "corner_frequencies/highpass",
            parameters={},
        )
        if self.fclp_checkbox_widget.value == True:
            data = np.asarray([self.fclp_display])
            self.workspace.dataset.add_auxiliary_data(
                data=data,
                data_type="review",
                path=path + "corner_frequencies/lowpass",
                parameters={},
            )
        data = np.asarray([1])
        timestamp = str(datetime.utcnow())
        parameters = {
            "username": self.workspace.config["user"]["name"],
            "timestamp": timestamp,
        }
        self.workspace.dataset.add_auxiliary_data(
            data=data, data_type="review", path=path + "accepted", parameters=parameters
        )
        self.human_review[self.NetSta + ", " + self.Cha]["reviewed"] = 1
        self.human_review[self.NetSta + ", " + self.Cha]["accepted"] = 1
        I = self.waveform_widget.options.index(self.waveform_widget.value)
        if (len(self.waveform_widget.options) > 1) and (
            I < len(self.waveform_widget.options) - 1
        ):
            self.waveform_widget.value = self.waveform_widget.options[I + 1]
            self.set_waveform_list(b)
        elif (len(self.waveform_widget.options) > 1) and (
            I == len(self.waveform_widget.options) - 1
        ):
            self.waveform_widget.value = self.waveform_widget.options[I - 1]
            self.set_waveform_list(b)
        else:
            self.set_waveform_list(b)
        self.fclp_checkbox_widget.value = True
        
        self.reviewed_count += 1
        self.progress_widget.value = self.reviewed_count 
        self.progress_widget.description="%s%s%s%s%s" % ("Progress (",self.reviewed_count,"/",self.total_count,"):") 
        return

    def reject_record(self, b):
        """
        Updates human_review instance variable in auxiliary_data upon press of reject_button.
        Args:
            b: Dummy variable needed to run Jupyter Widgets.
        """
        self.clear_plots()
        try:  # Delete auxiliary_data for record if it exists
            del self.workspace.dataset.auxiliary_data.review[self.NetSta][self.NCR]
        except:
            pass
        path = self.NetSta + "/" + self.NCR + "/"
        data = np.asarray([self.fchp_widget.value])
        self.workspace.dataset.add_auxiliary_data(
            data=data,
            data_type="review",
            path=path + "corner_frequencies/highpass",
            parameters={},
        )
        if self.fclp_checkbox_widget.value == True:
            data = np.asarray([self.fclp_display])
            self.workspace.dataset.add_auxiliary_data(
                data=data,
                data_type="review",
                path=path + "corner_frequencies/lowpass",
                parameters={},
            )
        data = np.asarray([0])
        timestamp = str(datetime.utcnow())
        parameters = {
            "username": self.workspace.config["user"]["name"],
            "timestamp": timestamp,
        }
        self.workspace.dataset.add_auxiliary_data(
            data=data, data_type="review", path=path + "accepted", parameters=parameters
        )
        self.human_review[self.NetSta + ", " + self.Cha]["reviewed"] = 1
        self.human_review[self.NetSta + ", " + self.Cha]["accepted"] = 0
        I = self.waveform_widget.options.index(self.waveform_widget.value)
        if (len(self.waveform_widget.options) > 1) and (
            I < len(self.waveform_widget.options) - 1
        ):
            self.waveform_widget.value = self.waveform_widget.options[I + 1]
            self.set_waveform_list(b)
        elif (len(self.waveform_widget.options) > 1) and (
            I == len(self.waveform_widget.options) - 1
        ):
            self.waveform_widget.value = self.waveform_widget.options[I - 1]
            self.set_waveform_list(b)
        else:
            self.set_waveform_list(b)
        self.fclp_checkbox_widget.value = True
        self.reviewed_count += 1
        self.progress_widget.value = self.reviewed_count 
        self.progress_widget.description="%s%s%s%s%s" % ("Progress (",self.reviewed_count,"/",self.total_count,"):") 
        return

    def clear_plots(self):
        """
        Clears plot objects prior to plotting new data.
        """
        for key, value in self.ln.items():
            value.set_data([0.01], [0.01])
        for key, value in self.ln_filt.items():
            value.set_xdata(x=0)
        for a1 in self.ax:
            for a in a1:
                a.relim()
                a.autoscale_view()
                a.grid(True, alpha=0.5, which="both")
        self.fig.canvas.draw()
        return