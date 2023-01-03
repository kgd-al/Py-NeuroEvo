from enum import IntFlag

import pytest


class TestSize(IntFlag):
    SMALL = 2
    NORMAL = 8
    LARGE = 32


flags = {
    TestSize.SMALL: "--fast",
    TestSize.NORMAL: "--normal-scale",
    TestSize.LARGE: "--full-scale",
}


def pytest_addoption(parser):
    parser.addoption(flags[TestSize.SMALL], "--small-scale",
                     action='store_const',
                     const=TestSize.SMALL, dest='size',
                     help='Run very small test suite '
                          '(single mutation case, 4 repeats...)')
    parser.addoption(flags[TestSize.NORMAL], action='store_const',
                     const=TestSize.NORMAL, default=TestSize.NORMAL,
                     dest='size',
                     help='Run moderate test suite '
                          '(two mutation cases, 8 repeats...)')
    parser.addoption(flags[TestSize.LARGE], action='store_const',
                     const=TestSize.LARGE, dest='size',
                     help='Run large test suite '
                          '(4 mutation cases, 16 repeats...). '
                          'Warning: While it ensures good coverage, it will'
                          ' take (too) long')

    default_dict = dict(
        seed=None,
        population=None,
        generations=None,
        fitness='depth'
    )

    def parse_evo_config(str_dict):
        provided_dict = {
            k: v for k, v in
            (kv.split(":") for kv in str_dict.strip("\"{}").split(","))
        }
        for k, v in provided_dict.items():
            if k in default_dict:
                default_dict[k] = type(default_dict[k])(v)
        return default_dict

    parser.addoption("--test-evolution", dest='evolution',
                     const=str(default_dict), nargs='?',
                     help=f"Run a mock evolution. Default arguments are:"
                          f" {default_dict}. Provide a dictionary to alter"
                          f" defaults arguments",
                     type=parse_evo_config)


best_ad_rate = .75


kgd_config = dict(
    seed={k: range(k) for k in TestSize},
    mutations={
        TestSize.SMALL: [10],
        TestSize.NORMAL: [100],
        TestSize.LARGE: [0, 1000]
    },
    ad_rate={
        TestSize.SMALL: [best_ad_rate],
        TestSize.NORMAL: [1],
        TestSize.LARGE: [2, .5]
    },

)


def values_for(key: str):
    values = []
    for v in kgd_config[key].values():
        values += v
    return sorted(set(values))


def scale_for(key: str, value):
    for ts in TestSize:
        if value in kgd_config[key][ts]:
            return ts


def max_scale_for(params):
    scale = TestSize.SMALL
    for k, v in params.items():
        if k in kgd_config:
            scale = max(scale, scale_for(k, v))
    return scale


def pytest_generate_tests(metafunc):
    def can_parametrize(name):
        if name not in metafunc.fixturenames:
            return False
        existing = [
            m for m in metafunc.definition.iter_markers('parametrize')
            if name in m.args[0]
        ]
        return len(existing) == 0

    def maybe_parametrize(name, short_name=None, values=None):
        if can_parametrize(name):
            # print(f"adding {name} = {values_for(name)}")
            if values is None:
                values = values_for(name)

            metafunc.parametrize(name, values,
                                 ids=lambda val: ""
                                 if short_name is None else
                                 f"{short_name}_{val}")

    # print("Configuring", metafunc.function)
    maybe_parametrize("mutations", "m")
    maybe_parametrize("seed", "s")
    maybe_parametrize("ad_rate", "ar")

    if can_parametrize("evo_config"):
        evo_config = metafunc.config.getoption('evolution')
        size = metafunc.config.getoption('size')
        sizes = {TestSize.SMALL: 1, TestSize.NORMAL: 2, TestSize.LARGE: 4}
        evo_config_values = [None for _ in range(sizes[size])]
        if evo_config is not None:
            for i in range(sizes[size]):
                dct = dict()

                def maybe_assign(key, if_true, if_false):
                    dct[key] = (if_true(evo_config[key]) if
                                evo_config[key] is not None else if_false)
                maybe_assign("seed", lambda s: s+1, i)
                maybe_assign("population", lambda s: s, 8*size)
                maybe_assign("generations", lambda s: s, 8*size)
                dct["fitness"] = evo_config["fitness"]
                evo_config_values[i] = dct

        maybe_parametrize("evo_config", short_name=None,
                          values=evo_config_values)


def pytest_collection_modifyitems(config, items):
    scale = config.getoption("size")
    slow_marks = {}
    for s_ in TestSize:
        if s_ <= scale:
            continue
        flag = flags[s_]
        slow_marks[s_] = \
            pytest.mark.skip(reason=f"Test scale ({s_.name}) is larger than"
                                    f" current target ({scale.name}). Use"
                                    f" {flag} to run")

    for item in items:
        if not hasattr(item, 'callspec'):
            continue

        if item.originalname == "test_evolution":
            if config.getoption('evolution') is None:
                item.add_marker(
                    pytest.mark.skip(reason="Only running evolution test on"
                                            " explicit request. Use"
                                            " --test-evolution=[dict] to do"
                                            " so.")
                )
            continue

        that_scale = max_scale_for(item.callspec.params)
        if scale < that_scale:
            item.add_marker(slow_marks[that_scale])
        # else:
        #     print(item, item.callspec)
