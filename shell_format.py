import os.path
import subprocess

import sublime
import sublime_plugin

SETTINGS_FILE_NAME = "shell_format.sublime-settings"


class BeautifyLatexOnSave(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        self.config = sublime.load_settings(SETTINGS_FILE_NAME)
        if self.config.get("run_on_save"):
            view.run_command("shell_format")


class ShellFormatCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.config = sublime.load_settings(SETTINGS_FILE_NAME)
        self.vars = self.view.window().extract_variables()

        if not self.is_shell_file:
            return

        self.reformat(edit)

    def get_command_line(self):
        cmd = self.config.get("shfmt_command", "shfmt")
        cmd = os.path.expanduser(cmd)
        cmd = sublime.expand_variables(cmd, self.vars)
        cmd = [cmd]

        options = self.config.get("shfmt_options", {})
        if options.get("simplify"):
            cmd.append("-s")

        shfmt_indent = options.get("indent")
        if shfmt_indent:
            cmd.extend(["-i", str(shfmt_indent)])

        if options.get("binary_ops_new_line"):
            cmd.append("-bn")

        if options.get("switch_case_indent"):
            cmd.append("-ci")

        if options.get("space_after_redirect"):
            cmd.append("-sr")

        if options.get("keep_paddings"):
            cmd.append("-kp")

        if options.get("minify"):
            cmd.append("-mn")

        return cmd

    def run_shfmt(self, cmd, cwd, content):
        p = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = p.communicate(input=content.encode("utf8"))
        return p.returncode, out, err

    def reformat(self, edit):
        buffer = sublime.Region(0, self.view.size())

        cmd = self.get_command_line()
        cwd = self.vars.get("file_path")
        content = self.view.substr(buffer)
        rcode, out, err = self.run_shfmt(cmd, cwd, content)

        if rcode == 0:
            self.view.replace(edit, buffer, out.decode("utf8"))
        else:
            sublime.error_message(err.decode("utf8"))

    @property
    def is_shell_file(self):
        legal_scopes = self.config.get("scopes", ["source.shell.bash"])
        actual_scopes = self.view.scope_name(0).split()
        return bool(set(legal_scopes) & set(actual_scopes))
