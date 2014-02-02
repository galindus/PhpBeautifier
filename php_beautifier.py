import re
import os
import subprocess

import sublime
import sublime_plugin


class PhpBeautifierCommand(sublime_plugin.TextCommand):
    def run(self, edit):        
        # Load settings
        settings = sublime.load_settings('PhpBeautifier.sublime-settings') 
        # Test environment
        if self.view.is_scratch():
            return

        if self.view.is_dirty():
            return self.error("Please save the file.")

        # check if file exists.
        FILE = self.view.file_name()
        if not FILE or not os.path.exists(FILE):
            return self.error("File {0} does not exist.".format(FILE))

        # check if extension is allowed.
        fileName, fileExtension = os.path.splitext(FILE)        
        if fileExtension[1:] not in settings.get('extensions'):
            if not self.missingFileExtension(fileExtension[1:], settings):
                return            

        # Start doing stuff
        cmd = "php_beautifier"

        # Load indent and filters settings        
        indent = settings.get('indent');
        filters = ' '.join(settings.get('filters'));
        
        allFile = sublime.Region(0, self.view.size())
        AllFileText = self.view.substr(allFile).encode('utf-8')

        if os.name == 'nt':
            cmd_win = cmd + ".bat"
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            p = subprocess.Popen([cmd_win, indent, "-l", filters, "-f", "-", "-o", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        else:
            p = subprocess.Popen([cmd, indent, "-l", filters, "-f", "-", "-o", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(AllFileText)
        if len(stderr) == 0:
            self.view.replace(edit, allFile, self.fixup(stdout))
            self.status("PhpBeautifier: File processed.")
        else:
            self.show_error_panel(self.fixup(stderr))

    # Error panel & fixup from external command
    # https://github.com/technocoreai/SublimeExternalCommand
    def show_error_panel(self, stderr):
        panel = self.view.window().get_output_panel("php_beautifier_errors")
        panel.set_read_only(False)
        edit = panel.begin_edit()
        panel.erase(edit, sublime.Region(0, panel.size()))
        panel.insert(edit, panel.size(), stderr)
        panel.set_read_only(True)
        self.view.window().run_command("show_panel", {"panel": "output.php_beautifier_errors"})
        panel.end_edit(edit)

    def fixup(self, string):
        return re.sub(r'\r\n|\r', '\n', string.decode('utf-8'))

    def status(self, string):
        return sublime.status_message(string)

    def error(self, string):
        return sublime.error_message(string)

    def missingFileExtension(self, fileExtension, settings):
        if sublime.ok_cancel_dialog("Extension {0} is not a valid php extension. Would you like to add this extension to your preferences?.".format(fileExtension), "Yes, add {0} extension to my preferences".format(fileExtension)):
            extensions = settings.get('extensions')
            extensions.append(fileExtension)
            settings.set('extensions', extensions)
            settings = sublime.save_settings('PhpBeautifier.sublime-settings')
            return True
        return False

