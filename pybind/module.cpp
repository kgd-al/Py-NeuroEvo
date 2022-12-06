#include "module.h"
namespace py = pybind11;

namespace kgd::eshn::pybind {

void init_genotype (py::module_ &m);
void init_cppn_phenotype (py::module_ &m);
void init_ann_phenotype (py::module_ &m);
void init_config (py::module_ &m);

PYBIND11_MODULE(_cpp, main) {
  main.doc() = "Docstring main module";

  auto genotype = main.def_submodule(
        "genotype",
        "Docstring for genotype submodule");
  init_genotype(genotype);

  auto phenotype = main.def_submodule(
        "phenotype",
        "Docstring for phenotype submodule");
  init_cppn_phenotype(phenotype);
  init_ann_phenotype(phenotype);

  auto config = main.def_submodule(
        "config",
        "Docstring for config submodule");
  init_config(config);

  auto misc = main.def_submodule(
        "misc",
        "Docstring for phenotype submodule");
}

} // kgd::eshn::pybind
