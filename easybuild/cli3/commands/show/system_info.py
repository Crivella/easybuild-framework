import sys

from easybuild.tools.systemtools import UNKNOWN, get_cpu_architecture, get_cpu_family
from easybuild.tools.systemtools import get_cpu_features, get_gpu_info, get_system_info

from . import show
from ...click_wrapper import click


def no_help_command(*args, **kwargs):
    """Decorator to create a command that is hidden from help output."""
    kwargs.setdefault('add_help_option', False)
    return show.command(*args, **kwargs)


@no_help_command()
def system_info():
    """Show system information."""
    system_info = get_system_info()
    cpu_features = get_cpu_features()
    gpu_info = get_gpu_info()
    cpu_arch_name = system_info['cpu_arch_name']
    lines = [
        "System information (%s):" % system_info['hostname'],
        '',
        "* OS:",
        "  -> name: %s" % system_info['os_name'],
        "  -> type: %s" % system_info['os_type'],
        "  -> version: %s" % system_info['os_version'],
        "  -> platform name: %s" % system_info['platform_name'],
        '',
        "* CPU:",
        "  -> vendor: %s" % system_info['cpu_vendor'],
        "  -> architecture: %s" % get_cpu_architecture(),
        "  -> family: %s" % get_cpu_family(),
    ]
    if cpu_arch_name == UNKNOWN:
        lines.append("  -> arch name: UNKNOWN (archspec is not installed?)")
    else:
        lines.append("  -> arch name: %s" % cpu_arch_name)

    lines.extend([
        "  -> model: %s" % system_info['cpu_model'],
        "  -> speed: %s" % system_info['cpu_speed'],
        "  -> cores: %s" % system_info['core_count'],
        "  -> features: %s" % ','.join(cpu_features),
    ])

    if gpu_info:
        lines.extend([
            '',
            "* GPU:",
        ])
        for vendor, vendor_gpu in gpu_info.items():
            lines.append("  -> %s" % vendor)
            for gpu, num in vendor_gpu.items():
                lines.append("    -> %sx %s" % (num, gpu))

    lines.extend([
        '',
        "* software:",
        "  -> glibc version: %s" % system_info['glibc_version'],
        "  -> Python binary: %s" % sys.executable,
        "  -> Python version: %s" % sys.version.split(' ')[0],
    ])

    click.echo("\n".join(lines))

__all__ = [
    'system_info',
]
