import os
import sys
import wx
import shutil
from PIL import Image
from tkinter import Tk
from tkinter import filedialog

def SelectTargetFolder():
    root = Tk()
    root.withdraw()
    target_dir = filedialog.askdirectory(title="Select Target Folder")
    root.destroy()
    return target_dir

def BuildPhotoList(target_dir):
    photo_list = sorted([f for f in os.listdir(target_dir) if f.lower().endswith('.jpg')])
    return photo_list

def NoValidData(parent=None):
    dialog = wx.MessageDialog(parent,
                              "No JPG files found in target folder. Exiting.",
                              "Error",
                              wx.OK | wx.ICON_INFORMATION)

    dialog.ShowModal()
    dialog.Destroy()

class PhotoViewer(wx.Frame):
    def __init__(self, parent, title, photo_list):
        super(PhotoViewer, self).__init__(parent, title=title, size=(1200, 800))

        self.Credit()

        self.photo_list = photo_list
        self.current_photo_index = 0

        icon = "icon.jpg"
        icon_dir = self.ResourcePath(icon)
        icon = wx.Icon(icon_dir, wx.BITMAP_TYPE_JPEG)
        self.SetIcon(icon)

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(25, 25, 25))  # Matching panel background
        panel.SetForegroundColour(wx.Colour(255, 255, 255))  # Matching panel text
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.selection_panel = wx.Panel(panel, size=(200, -1))
        self.selection_panel.SetBackgroundColour(wx.Colour(25, 25, 25))  # Matching selection panel background
        self.selection_panel.SetForegroundColour(wx.Colour(255, 255, 255))  # Matching selection panel text
        self.CreateSelectionPanel(self.selection_panel)
        self.image_panel = wx.Panel(panel)
        self.image_panel.SetBackgroundColour(wx.Colour(25, 25, 25))  # Matching image panel background
        self.image_panel.SetForegroundColour(wx.Colour(255, 255, 255))  # Matching image panel text


        sizer.Add(self.selection_panel, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.image_panel, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)

        self.Centre()
        self.Show()

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.SetShortcuts()

        self.ImageWindow(self.current_photo_index)

    # ==================================================================== #
    # GUI
    # ==================================================================== #
    def ResourcePath(self, image):
        """ Get absolute path to resource, works for dev and for PyInstaller
        """
        path = os.path.dirname(os.path.abspath(__file__))
        base_path = getattr(sys, '_MEIPASS', path)

        return os.path.join(base_path, image)

    def CreateSelectionPanel(self, panel):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.hole_id_text = None
        self.run_no_text = None
        self.depth_from_text = None
        self.depth_to_text = None

        # ==================================================================== #
        # Photo Label Details
        # ==================================================================== #
        def AddLabeledTextField(vbox, panel, label_text, field_name):
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(panel, label=label_text)
            text_ctrl = wx.TextCtrl(panel)

            text_ctrl.SetBackgroundColour(wx.Colour(56, 56, 56))
            text_ctrl.SetForegroundColour(wx.Colour(255, 255, 255))

            hbox.Add(label, 0, wx.ALIGN_CENTER | wx.ALL, 5)
            hbox.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 5)
            vbox.Add(hbox, 0, wx.EXPAND | wx.ALL, 5)
            setattr(self, field_name, text_ctrl)

        AddLabeledTextField(vbox, panel, "Hole ID:", "hole_id_text")
        AddLabeledTextField(vbox, panel, "Run No:", "run_no_text")
        AddLabeledTextField(vbox, panel, "Depth From:", "depth_from_text")
        AddLabeledTextField(vbox, panel, "Depth To:", "depth_to_text")

        # ==================================================================== #
        # Save, Sample, Archive
        # ==================================================================== #
        button_size = (100, 25)

        save_button = wx.Button(panel, label="Save Photo", size=button_size)
        sample_button = wx.Button(panel, label="Sample Photo", size=button_size)
        archive_button = wx.Button(panel, label="Archive Photo", size=button_size)

        save_button.SetBackgroundColour(wx.Colour(25, 25, 25))
        sample_button.SetBackgroundColour(wx.Colour(25, 25, 25))
        archive_button.SetBackgroundColour(wx.Colour(25, 25, 25))

        save_button.SetForegroundColour(wx.Colour(255, 255, 255))
        sample_button.SetForegroundColour(wx.Colour(255, 255, 255))
        archive_button.SetForegroundColour(wx.Colour(255, 255, 255))

        vbox.Add(save_button, 0, wx.CENTER | wx.ALL, 5)
        vbox.Add(sample_button, 0, wx.CENTER | wx.ALL, 5)
        vbox.Add(archive_button, 0, wx.CENTER | wx.ALL, 5)

        save_button.Bind(wx.EVT_BUTTON, self.SavePhoto)
        sample_button.Bind(wx.EVT_BUTTON, self.SamplePhoto)
        archive_button.Bind(wx.EVT_BUTTON, self.ArchivePhoto)

        vbox.AddStretchSpacer(1) # Push Next & Last to base of panel

        # ==================================================================== #
        # Rotate Buttons
        # ==================================================================== #
        rotate_hbox = wx.BoxSizer(wx.HORIZONTAL)

        rotate_left_button = wx.Button(panel, label="Rotate Left")
        rotate_right_button = wx.Button(panel, label="Rotate Right")

        rotate_left_button.SetBackgroundColour(wx.Colour(25, 25, 25))
        rotate_right_button.SetBackgroundColour(wx.Colour(25, 25, 25))

        rotate_left_button.SetForegroundColour(wx.Colour(255, 255, 255))
        rotate_right_button.SetForegroundColour(wx.Colour(255, 255, 255))

        rotate_hbox.Add(rotate_left_button, 1, wx.EXPAND | wx.ALL, 5)
        rotate_hbox.Add(rotate_right_button, 1, wx.EXPAND | wx.ALL, 5)

        vbox.Add(rotate_hbox, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        rotate_left_button.Bind(wx.EVT_BUTTON, self.RotateLeft)
        rotate_right_button.Bind(wx.EVT_BUTTON, self.RotateRight)

        # ==================================================================== #
        # Next and Last Buttons
        # ==================================================================== #
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        last_button = wx.Button(panel, label="Last Photo")
        next_button = wx.Button(panel, label="Next Photo")

        last_button.SetBackgroundColour(wx.Colour(25, 25, 25))
        next_button.SetBackgroundColour(wx.Colour(25, 25, 25))

        last_button.SetForegroundColour(wx.Colour(255, 255, 255))
        next_button.SetForegroundColour(wx.Colour(255, 255, 255))

        hbox.Add(last_button, 1, wx.EXPAND | wx.ALL, 5)
        hbox.Add(next_button, 1, wx.EXPAND | wx.ALL, 5)

        next_button.Bind(wx.EVT_BUTTON, self.NextPhoto)
        last_button.Bind(wx.EVT_BUTTON, self.LastPhoto)

        vbox.Add(hbox, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        panel.SetSizer(vbox)

    def Credit(self, ):
        dialog = wx.MessageDialog(self,
                            "Created and maintained by Christopher Lien",
                            "Credit",
                            wx.OK | wx.ICON_INFORMATION)

        dialog.ShowModal()
        dialog.Destroy()

    def ImageWindow(self, photo_index):
        photo_path = os.path.join(target_dir, self.photo_list[photo_index])
        image = wx.Image(photo_path, wx.BITMAP_TYPE_ANY)

        def ScaleImage(image):
            window_width, window_height = self.image_panel.GetSize()

            image_width = image.GetWidth()
            width_ratio = window_width / image_width

            image_height = image.GetHeight()
            height_ratio = window_height / image_height

            image_scaling_factor = min(width_ratio, height_ratio)

            new_image_width = int(image_width * image_scaling_factor)
            new_image_height = int(image_height * image_scaling_factor)

            image = image.Scale(new_image_width, new_image_height, wx.IMAGE_QUALITY_HIGH)

            return image

        image = ScaleImage(image)

        self.image_panel.DestroyChildren()
        bitmap = wx.StaticBitmap(self.image_panel, -1, wx.Bitmap(image))

        sizer = wx.BoxSizer(wx.VERTICAL)
        center_sizer = wx.BoxSizer(wx.HORIZONTAL)
        center_sizer.Add(bitmap, 0, wx.ALIGN_CENTER)
        sizer.Add(center_sizer, 1, wx.ALIGN_CENTER)

        self.image_panel.SetSizer(sizer)
        self.image_panel.Layout()

    # ==================================================================== #
    # Keyboard Shortcuts
    # ==================================================================== #
    def OnClose(self, event):
        self.Destroy()

    def SetShortcuts(self):
        rotate_right_id = wx.NewIdRef()
        save_photo_id = wx.NewIdRef()
        last_photo_id = wx.NewIdRef()
        next_photo_id = wx.NewIdRef()

        shortcut = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('R'), rotate_right_id),
            (wx.ACCEL_CTRL, ord('S'), save_photo_id),
            (wx.ACCEL_NORMAL, wx.WXK_LEFT, last_photo_id),
            (wx.ACCEL_NORMAL, wx.WXK_RIGHT, next_photo_id)
        ])

        self.SetAcceleratorTable(shortcut)

        self.Bind(wx.EVT_MENU, self.RotateRight, id=rotate_right_id)
        self.Bind(wx.EVT_MENU, self.SavePhoto, id=save_photo_id)
        self.Bind(wx.EVT_MENU, self.LastPhoto, id=last_photo_id)
        self.Bind(wx.EVT_MENU, self.NextPhoto, id=next_photo_id)

    # ==================================================================== #
    # Update & Get
    # ==================================================================== #
    def UpdateImage(self, ):
        if len(self.photo_list) > 0:
            self.current_photo_index = (self.current_photo_index) % len(self.photo_list)
            self.ImageWindow(self.current_photo_index)
        else:
            dialog = wx.MessageDialog(self,
                                    "No Photos Remaining.",
                                    "Missing Data",
                                    wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()

    def GetImagePath(self, ):
        try:
            photo_path = os.path.join(target_dir, self.photo_list[self.current_photo_index])

            return photo_path

        except (IndexError, FileNotFoundError) as e:
            dialog = wx.MessageDialog(self,
                                "No Photos Remaining.",
                                "Missing Data",
                                wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            pass

    # ==================================================================== #
    # Save, Sample and Archive Photos
    # ==================================================================== #
    def Validation(self, hole_id, run_no, depth_from, depth_to):

        # ==================================================================== #
        # Cells not None
        # ==================================================================== #
        if not hole_id or not run_no or not depth_from or not depth_to:
            dialog = wx.MessageDialog(self,
                                    "All fields must have data. Please ensure no field is empty.",
                                    "Missing Data",
                                    wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            return False

        # ==================================================================== #
        # Run No valid
        # ==================================================================== #
        try:
            run_no = int(run_no)
        except ValueError:
            dialog = wx.MessageDialog(self,
                                    "Run No must be an integer. Please enter a valid number.",
                                    "Invalid Run No",
                                    wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            return False

        # ==================================================================== #
        # Depth From valid
        # ==================================================================== #
        try:
            depth_from = float(depth_from)
            if not depth_from == float(f"{depth_from:.2f}"):
                raise ValueError()
        except ValueError:
            dialog = wx.MessageDialog(self,
                                    "Depth From must be a float with max two decimal places (e.g., 444.49).",
                                    "Invalid Depth From",
                                    wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            return False

        # ==================================================================== #
        # Depth To valid
        # ==================================================================== #
        try:
            depth_to = float(depth_to)
            if not depth_to == float(f"{depth_to:.2f}"):
                raise ValueError()
        except ValueError:
            dialog = wx.MessageDialog(self,
                                    "Depth To must be a float with max two decimal places (e.g., 27.23).",
                                    "Invalid Depth To",
                                    wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            return False

        return True

    def SavePhoto(self, event):
        hole_id = self.hole_id_text.GetValue()
        run_no = self.run_no_text.GetValue()
        depth_from = self.depth_from_text.GetValue()
        depth_to = self.depth_to_text.GetValue()

        if not self.Validation(hole_id, run_no, depth_from, depth_to):
            return

        save_folder = self.CreateSaveFolder()
        backup_folder = self.CreateBackupFolder()

        photo_path = self.GetImagePath()
        photo_name = self.photo_list[self.current_photo_index]

        shutil.copy(photo_path, save_folder)
        shutil.copy(photo_path, backup_folder)
        os.remove(photo_path)

        depth_to = float(depth_to)
        formatted_depth_from = format(float(depth_from), '.2f')
        formatted_depth_to = format(depth_to, '.2f')

        new_photo_name = f"{hole_id}_Run_{run_no}_{formatted_depth_from}-{formatted_depth_to}{os.path.splitext(photo_name)[1]}"
        new_photo_path = os.path.join(save_folder, new_photo_name)
        os.rename(os.path.join(save_folder, photo_name), new_photo_path)

        # Modulate values to 0.50 intervals.
        remainder = depth_to % 0.50
        if remainder == 0:
            value = 0.50
        else:
            value = 0.50 - remainder

        new_depth_to = depth_to + value

        formatted_new_depth_to = format(new_depth_to, '.2f')

        self.depth_to_text.SetValue(formatted_new_depth_to)
        self.depth_from_text.SetValue(formatted_depth_to)

        del self.photo_list[self.current_photo_index]
        self.UpdateImage()

    def SamplePhoto(self, event):
        sample_folder = self.CreateSampleFolder()
        backup_folder = self.CreateBackupFolder()

        photo_path = self.GetImagePath()

        shutil.copy(photo_path, sample_folder)
        shutil.copy(photo_path, backup_folder)
        os.remove(photo_path)

        del self.photo_list[self.current_photo_index]
        self.UpdateImage()

    def ArchivePhoto(self, event):
        archive_folder = self.CreateArchiveFolder()
        backup_folder = self.CreateBackupFolder()
        photo_path = self.GetImagePath()

        shutil.copy(photo_path, archive_folder)
        shutil.copy(photo_path, backup_folder)
        os.remove(photo_path)

        del self.photo_list[self.current_photo_index]
        self.UpdateImage()

    # ==================================================================== #
    # Rotate Photos
    # ==================================================================== #
    def RotateLeft(self, event):
        photo_path = self.GetImagePath()
        image = Image.open(photo_path)
        image = image.rotate(90, expand=True)
        image.save(photo_path)

        self.ImageWindow(self.current_photo_index)

    def RotateRight(self, event):
        photo_path = self.GetImagePath()
        image = Image.open(photo_path)
        image = image.rotate(270, expand=True)
        image.save(photo_path)

        self.ImageWindow(self.current_photo_index)

    # ==================================================================== #
    # Next and Last Photos
    # ==================================================================== #
    def NextPhoto(self, event):
        self.current_photo_index = (self.current_photo_index + 1) % len(self.photo_list)
        self.ImageWindow(self.current_photo_index)

    def LastPhoto(self, event):
        self.current_photo_index = (self.current_photo_index - 1) % len(self.photo_list)
        self.ImageWindow(self.current_photo_index)

    # ==================================================================== #
    # Create folders
    # ==================================================================== #
    def CreateSaveFolder(self, ):
        save_folder = os.path.join(target_dir, "Run Photo")
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        return save_folder

    def CreateSampleFolder(self, ):
        sample_folder = os.path.join(target_dir, "Sample Photo")
        if not os.path.exists(sample_folder):
            os.makedirs(sample_folder)

        return sample_folder

    def CreateArchiveFolder(self, ):
        archive_folder = os.path.join(target_dir, "Archive Photo")
        if not os.path.exists(archive_folder):
            os.makedirs(archive_folder)

        return archive_folder

    def CreateBackupFolder(self, ):
        backup_folder = os.path.join(target_dir, "Backup")
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)

        return backup_folder

if __name__ == '__main__':
    target_dir = SelectTargetFolder()
    photo_list = BuildPhotoList(target_dir)
    if photo_list:
        app = wx.App(False)
        frame = PhotoViewer(None, "Photo Viewer", photo_list)
        app.MainLoop()
    else:
        app = wx.App(False)
        NoValidData()