from typing import Sequence, Tuple

import click
from click.formatting import measure_table, iter_rows


class OrderedCommand(click.Command):
    def get_params(self, ctx):
        rv = super().get_params(ctx)
        rv.sort(key=lambda o: (not o.required, o.name))
        return rv

    def format_options(self, ctx, formatter) -> None:
        """Writes all the options into the formatter if they exist."""
        opts = []
        for param in self.get_params(ctx):
            rv = param.get_help_record(ctx)
            if rv is not None:
                opts.append(rv)

        if opts:
            with formatter.section("Options"):
                self.write_dl(formatter, opts)

    @staticmethod
    def write_dl(formatter, rows: Sequence[Tuple[str, str]], col_max: int = 30, col_spacing: int = 2) -> None:
        rows = list(rows)
        widths = measure_table(rows)
        if len(widths) != 2:
            raise TypeError("Expected two columns for definition list")

        first_col = min(widths[0], col_max) + col_spacing

        for first, second in iter_rows(rows, len(widths)):
            formatter.write(f"{'':>{formatter.current_indent}}{first}")
            if not second:
                formatter.write("\n")
                continue
            if len(first) <= first_col - col_spacing:
                formatter.write(" " * (first_col - len(first)))
            else:
                formatter.write("\n")
                formatter.write(" " * (first_col + formatter.current_indent))

            if "[" in second:
                text, meta = second.split("[")
                formatter.write(f"[{meta} {text}\n")
            else:
                formatter.write(f"{second}\n")
