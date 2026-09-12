from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

import plume_experiment
from plume_fly import root_side_of


def test_female_sides():
    brain = SimpleNamespace(soma_side=np.array(['L', 'R', '']),
                            where=lambda **kw: np.array([0, 1]))
    assert root_side_of(brain).tolist() == ['L', 'R', '']
    brain.soma_side[1] = ''
    with pytest.raises(ValueError, match='unresolved'):
        root_side_of(brain)


def test_published_hardlink(tmp_path):
    published = tmp_path / 'published.json'
    published.write_text('{}', encoding='utf-8')
    alias = tmp_path / 'alias_experiment.json'
    alias.hardlink_to(published)
    with patch.object(plume_experiment, 'PUBLISHED_V1', [published]):
        with pytest.raises(ValueError, match='refusing'):
            plume_experiment.assert_not_published(tmp_path / 'alias')


def test_unpublished_output(tmp_path):
    published = tmp_path / 'published.json'
    published.write_text('{}', encoding='utf-8')
    with patch.object(plume_experiment, 'PUBLISHED_V1', [published]):
        plume_experiment.assert_not_published(tmp_path / 'fresh')
