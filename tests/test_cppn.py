import pydoc
from random import Random

import numpy as np
from PIL import Image
from pytest_steps import test_steps

from abrain._cpp.phenotype import ( # noqa
    CPPN, Point,
)
from abrain.core.genome import Genome


def _make_cppn(seed, mutations=0):
    rng = Random(seed)
    genome = Genome.random(rng)
    for _ in range(mutations):
        genome.mutate(rng)
    try:
        cppn = CPPN(genome)
    except Exception as e:  # pragma: no cover
        genome.to_dot("foo.pdf", debug="depths,links")
        raise e
    return cppn, genome


def test_exists():
    cppn = _make_cppn(16)
    print(cppn)
    print(pydoc.render_doc(cppn))
    print(pydoc.render_doc(CPPN.Output))
    print(CPPN.Output.Weight)
    print(CPPN.OUTPUTS_LIST)
    assert CPPN.Output.Weight in CPPN.OUTPUTS_LIST


def test_functions():
    for k, v in CPPN.functions().items():
        print(f"{k}(0) = {v(0)}")


def test_create(seed):
    cppn = _make_cppn(seed)
    print(cppn)


def test_output_single(seed):
    cppn, _ = _make_cppn(seed)
    p0, p1 = Point(0., 0., 0.), Point(0., 0., 0.)
    for o in CPPN.OUTPUTS_LIST:
        values = set()
        for i in range(100):
            values.add(cppn(p0, p1, o))
        assert len(values) == 1


def test_outputs_all(seed):
    cppn, _ = _make_cppn(seed)
    p0, p1 = Point(0., 0., 0.), Point(0., 0., 0.)
    values = {k: set() for k in CPPN.OUTPUTS_LIST}
    outputs = CPPN.outputs()
    for i in range(100):
        cppn(p0, p1, outputs)
        for o in CPPN.OUTPUTS_LIST:
            values[o].add(outputs[o])

    for o in CPPN.OUTPUTS_LIST:
        assert len(values[o]) == 1


def test_outputs_subset(seed):
    cppn, _ = _make_cppn(seed)
    p0, p1 = Point(0., 0., 0.), Point(0., 0., 0.)
    values = {k: set() for k in CPPN.OUTPUTS_LIST}
    subset = {CPPN.Output.Weight, CPPN.Output.LEO}
    outputs = CPPN.outputs()
    for i in range(100):
        cppn(p0, p1, outputs, subset)
        for o in CPPN.OUTPUTS_LIST:
            values[o].add(outputs[o])

    for o in CPPN.OUTPUTS_LIST:
        assert len(values[o]) == 1


def test_outputs_equals(seed):
    cppn, _ = _make_cppn(seed)

    rng = Random(seed)

    def r():
        return rng.uniform(-1, 1)

    def p():
        return Point(r(), r(), r())

    for i in range(100):
        p0, p1 = p(), p()

        manual_outputs = []
        for o in CPPN.OUTPUTS_LIST:
            manual_outputs.append(cppn(p0, p1, o))

        outputs = CPPN.outputs()
        cppn(p0, p1, outputs, {o for o in CPPN.OUTPUTS_LIST})
        subset_outputs = [outputs[i] for i in range(len(outputs))]

        cppn(p0, p1, outputs)
        all_outputs = [outputs[i] for i in range(len(outputs))]

        assert manual_outputs == subset_outputs
        assert manual_outputs == all_outputs


sample_sizes = [10, 50, 100]


@test_steps('generate_cppn', *[f"sample_at_{s}" for s in sample_sizes])
def test_multiscale_sampling(mutations, seed,
                             tmp_path_factory):  # pragma: no cover
    folder = tmp_path_factory.mktemp(numbered=False,
                                     basename=f"test_multiscale_sampling_"
                                              f"s{seed}_m{mutations}")

    cppn, genome = _make_cppn(seed, mutations)

    genome.to_dot(f"{folder}/cppn.png")
    print('Generated', f"{folder}/cppn.png")

    yield 'generate_cppn'

    dp = Point(0, 0, 0)
    for size in sample_sizes:
        def to_substrate_coord(index):
            return 2 * index / (size - 1) - 1

        data = np.zeros((2, size, size, 3), dtype=np.uint8)
        outputs = CPPN.outputs()

        for i in range(size):
            x = to_substrate_coord(i)
            for j in range(size):
                y = to_substrate_coord(j)
                p = Point(x, y, 0)
                for k, p0, p1 in [(0, p, dp), (1, dp, p)]:
                    cppn(p, dp, outputs)
                    data[k, i, j] = \
                        .5 * (
                            np.array([outputs[i] for i in range(len(outputs))])
                            + 1
                        ) * 255

        for name, i in [('input', 0), ('output', 1)]:
            file = f"{folder}/xy_{name}_plane_{size:03}x{size:03}.png"
            img = Image.fromarray(data[i])
            img.save(file)
            print('Generated', file)

        yield f"sample_at_{size}"
