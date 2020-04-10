# This file sets up tests for fundamental QC methods for the purpose
#  of developing and maintaining harnesses to check that a QC program runs
#  through QCEngine, that it returns properties as expected for the method,
#  and that those results have the same answers as other programs. For
#  new programs, try to add the six rhf/uhf/rohf ae/fc combinations to
#  each method (separate "def test..."). Common things to account for are
#  sph/cart basis sets, fc/ae defaults, semicanonical orbitals.
#  Feel free to add test case variations to check keyword handling.

# Handling/Testing Errors
# -----------------------
# * (E1) Calculation that QC program just can't run.
#   example: GAMESS UHF CC
#   handle: add "error" tuple to test like `_q2`
#   result: runner executes through pytest.raises so test passes
#
# * (E2) Calculation that QC program can run but full properties data not harvestable.
#   example: Psi4 run with dfocc module doesn't split out MP2 spin components for RHF
#   handle: add logic in `contractual_mp2` (or appropriate fn) to forgive specific properties
#   result: runner checks that expected props are present and unexpected are absent.
#           even if full properties not available, QC code is working normally, so test passes
#
# * (E3) Testing instance parameters not evenly available to QC programs.
#   example: Odd basis like QZ2P not in Q-Chem's library
#   handle: add pytest.skip at most general position
#   result: test registers but skipped
#
# * (E4) Calculation the QC program thinks it can run but we know better -- `return_result` wrong.
#   example: NWChem ROHF MP2 that's missing singles contribution
#   handle: add "wrong" typle to test like `_w1`
#   result: runner checks assertion fails at expected result and triggers pytest.xfail


import pytest
import qcelemental as qcel

import qcengine as qcng
from qcengine.programs.tests.standard_suite_ref import std_molecules, std_refs
from qcengine.testing import using

from .standard_suite_runner import runner_asserter

_basis_keywords = ["cfour_basis", "basis"]


@pytest.fixture
def clsd_open_pmols():
    return {
        name[:-4]: qcel.models.Molecule.from_data(smol, name=name[:-4])
        for name, smol in std_molecules.items()
        if name.endswith("-xyz")
    }


# yapf: disable
_q1 = (qcng.exceptions.InputError, "unknown SCFTYPE")  # no rohf reference for nwc mp2
_q2 = (qcng.exceptions.InputError, "CCTYP IS PROGRAMMED ONLY FOR SCFTYP=RHF OR ROHF")
_q3 = (qcng.exceptions.InputError, "ccsd: nopen is not zero")

_w1 = ("MP2 CORRELATION ENERGY", "nonstandard answer: NWChem TCE MP2 doesn't report singles (affects ROHF)")
_w2 = ("CCSD CORRELATION ENERGY", "nonstandard answer: GAMESS CCSD ROHF FC energy")
# yapf: enable


def _trans_key(qc, bas, key):
    # note that cfour isn't ready for keywords.basis instead of model.basis
    lkey = key.lower()

    # translate basis
    if lkey == "basis":
        return bas
    if bas.lower() == "cc-pvdz":
        if lkey == "cfour_basis":
            return "pvdz"
        elif lkey == "qcng_basis":
            if qc == "cfour":
                return "pvdz", {}
            elif qc == "gamess":
                return "ccd", {"contrl__ispher": 1}
            elif qc == "nwchem":
                return "cc-pvdz", {"basis__spherical": True}
            elif qc == "psi4":
                return bas, {}
            elif qc == "qchem":
                return "cc-pvdz", {}
    elif bas.lower() == "aug-cc-pvdz":
        if lkey == "cfour_basis":
            return "aug-pvdz"
        elif lkey == "qcng_basis":
            if qc == "cfour":
                return "aug-pvdz", {}
            elif qc == "gamess":
                return "accd", {"contrl__ispher": 1}
            elif qc == "nwchem":
                return "aug-cc-pvdz", {"basis__spherical": True}
            elif qc == "psi4":
                return bas, {}
            elif qc == "qchem":
                return "aug-cc-pvdz", {}
    elif bas.lower() == "cfour-qz2p":
        if lkey == "cfour_basis":
            return "qz2p"
        elif lkey == "qcng_basis":
            if qc == "cfour":
                return "qz2p", {}
            elif qc == "gamess":
                return None, {}  # not in GAMESS-US library
            elif qc == "nwchem":
                return None, {}  # not in NWChem library
            elif qc == "psi4":
                return bas, {}
            elif qc == "qchem":
                return None, {}  # not in Q-Chem library

    sys.exit(1)


@pytest.mark.parametrize("dertype", [0,], ids=["ene0"])
@pytest.mark.parametrize(
    "basis, subjects",
    [
        pytest.param("cc-pvdz", ["hf", "bh3p", "bh3p"], id="dz"),
        pytest.param("aug-cc-pvdz", ["h2o", "nh2", "nh2"], id="adz"),
        pytest.param("cfour-qz2p", ["h2o", "nh2", "nh2"], id="qz2p"),
    ],
)
@pytest.mark.parametrize(
    "inp",
    [
        # yapf: disable
        pytest.param({"call": "cfour",  "reference": "rhf",  "fcae": "ae", "keywords": {"scf_conv": 12},                                                             }, id="mp2  rhf ae: cfour",      marks=using("cfour")),
        pytest.param({"call": "gamess", "reference": "rhf",  "fcae": "ae", "keywords": {"mp2__nacore": 0},                                                           }, id="mp2  rhf ae: gamess",     marks=using("gamess")),
        pytest.param({"call": "nwchem", "reference": "rhf",  "fcae": "ae", "keywords": {"qc_module": "tce"},                                                         }, id="mp2  rhf ae: nwchem-tce", marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "rhf",  "fcae": "ae", "keywords": {},                                                                           }, id="mp2  rhf ae: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "psi4",   "reference": "rhf",  "fcae": "ae", "keywords": {"mp2_type": "conv"},                                                         }, id="mp2  rhf ae: psi4",       marks=using("psi4_mp2qcsk")),
        pytest.param({"call": "qchem",  "reference": "rhf",  "fcae": "ae", "keywords": {"N_FROZEN_CORE": 0},                                                         }, id="mp2  rhf ae: qchem",      marks=using("qchem")),

        pytest.param({"call": "cfour",  "reference": "rhf",  "fcae": "fc", "keywords": {"dropmo": 1, "scf_conv": 12},                                                }, id="mp2  rhf fc: cfour",      marks=using("cfour")),
        pytest.param({"call": "gamess", "reference": "rhf",  "fcae": "fc", "keywords": {},                                                                           }, id="mp2  rhf fc: gamess",     marks=using("gamess")),
        pytest.param({"call": "nwchem", "reference": "rhf",  "fcae": "fc", "keywords": {"qc_module": "tce", "tce__freeze": 1},                                       }, id="mp2  rhf fc: nwchem-tce", marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "rhf",  "fcae": "fc", "keywords": {"mp2__freeze": 1},                                                           }, id="mp2  rhf fc: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "rhf",  "fcae": "fc", "keywords": {"mp2__freeze__core": 1},                                                     }, id="mp2  rhf fc: nwchem",     marks=using("nwchem")),
        #pytest.param({"call": "nwchem", "reference": "rhf",  "fcae": "fc", "keywords": {"mp2__freeze__core__atomic": True},                                          }, id="mp2  rhf fc: nwchem",     marks=using("nwchem")),  # uses qcdb alias
        pytest.param({"call": "nwchem", "reference": "rhf",  "fcae": "fc", "keywords": {"mp2__freeze__atomic": {"O": 1}},                                            }, id="mp2  rhf fc: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "psi4",   "reference": "rhf",  "fcae": "fc", "keywords": {"freeze_core": True, "mp2_type": "conv"},                                    }, id="mp2  rhf fc: psi4",       marks=using("psi4_mp2qcsk")),

        pytest.param({"call": "cfour",  "reference": "uhf",  "fcae": "ae", "keywords": {"reference": "uhf", "scf_conv": 12},                                         }, id="mp2  uhf ae: cfour",      marks=using("cfour")),
        pytest.param({"call": "gamess", "reference": "uhf",  "fcae": "ae", "keywords": {"contrl__scftyp": "uhf", "mp2__nacore": 0},                                  }, id="mp2  uhf ae: gamess",     marks=using("gamess")),
        pytest.param({"call": "nwchem", "reference": "uhf",  "fcae": "ae", "keywords": {"qc_module": "tce", "scf__uhf": True},                                       }, id="mp2  uhf ae: nwchem-tce", marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "uhf",  "fcae": "ae", "keywords": {"scf__uhf": True},                                                           }, id="mp2  uhf ae: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "psi4",   "reference": "uhf",  "fcae": "ae", "keywords": {"reference": "uhf", "mp2_type": "conv"},                                     }, id="mp2  uhf ae: psi4",       marks=using("psi4_mp2qcsk")),

        pytest.param({"call": "cfour",  "reference": "uhf",  "fcae": "fc", "keywords": {"reference": "uhf", "dropmo": 1, "scf_conv": 12},                            }, id="mp2  uhf fc: cfour",      marks=using("cfour")),
        pytest.param({"call": "gamess", "reference": "uhf",  "fcae": "fc", "keywords": {"contrl__scftyp": "uhf"},                                                    }, id="mp2  uhf fc: gamess",     marks=using("gamess")),
        pytest.param({"call": "nwchem", "reference": "uhf",  "fcae": "fc", "keywords": {"qc_module": "tce", "tce__freeze": 1, "scf__uhf": True},                     }, id="mp2  uhf fc: nwchem-tce", marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "uhf",  "fcae": "fc", "keywords": {"scf__uhf": True, "mp2__freeze": 1},                                         }, id="mp2  uhf fc: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "psi4",   "reference": "uhf",  "fcae": "fc", "keywords": {"reference": "uhf", "freeze_core": True, "mp2_type": "conv"},                }, id="mp2  uhf fc: psi4",       marks=using("psi4_mp2qcsk")),
        pytest.param({"call": "qchem",  "reference": "uhf",  "fcae": "fc", "keywords": {"N_frozen_CORE": "fC"},                                                      }, id="mp2  uhf fc: qchem",      marks=using("qchem")),

        pytest.param({"call": "cfour",  "reference": "rohf", "fcae": "ae", "keywords": {"reference": "rohf", "scf_conv": 12},                                        }, id="mp2 rohf ae: cfour",      marks=using("cfour")),
        pytest.param({"call": "gamess", "reference": "rohf", "fcae": "ae", "keywords": {"contrl__scftyp": "rohf", "mp2__nacore": 0, "mp2__ospt": "RMP"},             }, id="mp2 rohf ae: gamess",     marks=using("gamess")),
        pytest.param({"call": "nwchem", "reference": "rohf", "fcae": "ae", "keywords": {"qc_module": "tce", "scf__rohf": True, "scf__thresh": 8,
                                                                                         "tce__thresh": 8, "tce__freeze": 0, "scf__tol2e": 10},          "wrong": _w1}, id="mp2 rohf ae: nwchem-tce", marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "rohf", "fcae": "ae", "keywords": {"scf__rohf": True},                                              "error": _q1}, id="mp2 rohf ae: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "psi4",   "reference": "rohf", "fcae": "ae", "keywords": {"reference": "rohf", "mp2_type": "conv"},                                    }, id="mp2 rohf ae: psi4",       marks=using("psi4_mp2qcsk")),

        pytest.param({"call": "cfour",  "reference": "rohf", "fcae": "fc", "keywords": {"reference": "rohf", "dropmo": 1, "scf_conv": 12},                           }, id="mp2 rohf fc: cfour",      marks=using("cfour")),
        pytest.param({"call": "gamess", "reference": "rohf", "fcae": "fc", "keywords": {"contrl__scftyp": "rohf", "mp2__ospt": "RMP"},                               }, id="mp2 rohf fc: gamess",     marks=using("gamess")),
        pytest.param({"call": "nwchem", "reference": "rohf", "fcae": "fc", "keywords": {"qc_module": "tce", "tce__freeze": 1, "scf__rohf": True},        "wrong": _w1}, id="mp2 rohf fc: nwchem-tce", marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "rohf", "fcae": "fc", "keywords": {"scf__rohf": True, "mp2__freeze": 1},                            "error": _q1}, id="mp2 rohf fc: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "psi4",   "reference": "rohf", "fcae": "fc", "keywords": {"reference": "rohf", "freeze_core": True, "mp2_type": "conv"},               }, id="mp2 rohf fc: psi4",       marks=using("psi4_mp2qcsk")),
        # yapf: enable
    ],
)
def test_mp2_energy_module(inp, dertype, basis, subjects, clsd_open_pmols, request):
    method = "mp2"
    qcprog = inp["call"]
    tnm = request.node.name
    subject = clsd_open_pmols[subjects[std_refs.index(inp["reference"])]]

    inpcopy = {k: v for k, v in inp.items()}
    inpcopy["keywords"] = {
        k: (_trans_key(qcprog, basis, k) if v == "<>" else v) for k, v in inpcopy["keywords"].items()
    }

    inpcopy["driver"] = "energy"
    if not any([k.lower() in _basis_keywords for k in inpcopy["keywords"]]):
        inpcopy["basis"], basis_extras = _trans_key(qcprog, basis, "qcng_basis")
        inpcopy["keywords"].update(basis_extras)
    inpcopy["scf_type"] = "pk"
    inpcopy["corl_type"] = "conv"
    inpcopy["qc_module"] = "-".join(
        [
            qcprog,
            inp["keywords"].get(
                "qc_module", inp["keywords"].get("cfour_cc_program", inp["keywords"].get("cc_program", ""))
            ),
        ]
    ).strip("-")
    print("INP", inpcopy)

    runner_asserter(inpcopy, subject, method, basis, tnm)


@pytest.mark.parametrize("dertype", [0,], ids=["ene0"])
@pytest.mark.parametrize(
    "basis, subjects",
    [
        pytest.param("cc-pvdz", ["hf", "bh3p", "bh3p"], id="dz"),
        pytest.param("aug-cc-pvdz", ["h2o", "nh2", "nh2"], id="adz"),
        pytest.param("cfour-qz2p", ["h2o", "nh2", "nh2"], id="qz2p"),
    ],
)
@pytest.mark.parametrize(
    "inp",
    [
        # yapf: disable
        pytest.param({"call": "cfour",  "reference": "rhf",  "fcae": "ae", "keywords": {"SCF_CONV": 12, "CC_CONV": 12, "cc_program": "vcc", "print": 2},                                                                 }, id="ccsd  rhf ae: cfour-vcc",  marks=using("cfour")),
        pytest.param({"call": "cfour",  "reference": "rhf",  "fcae": "ae", "keywords": {"SCF_CONV": 12, "CC_CONV": 12, "cc_program": "ecc",},                                                                            }, id="ccsd  rhf ae: cfour-ecc",  marks=using("cfour")),
        pytest.param({"call": "cfour",  "reference": "rhf",  "fcae": "ae", "keywords": {"SCF_CONV": 12, "CC_CONV": 12, "cc_program": "ncc",},                                                                            }, id="ccsd  rhf ae: cfour-ncc",  marks=using("cfour")),
      # pytest.param({"call": "cfour",  "reference": "rhf",  "fcae": "ae", "keywords": {},                                                                                                                               }, id="ccsd  rhf ae: cfour",      marks=using("cfour")),
        pytest.param({"call": "gamess", "reference": "rhf",  "fcae": "ae", "keywords": {"ccinp__ncore": 0},                                                                                                              }, id="ccsd  rhf ae: gamess",     marks=using("gamess")),
        pytest.param({"call": "nwchem", "reference": "rhf",  "fcae": "ae", "keywords": {"qc_module": "tce"},                                                                                                             }, id="ccsd  rhf ae: nwchem-tce", marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "rhf",  "fcae": "ae", "keywords": {},                                                                                                                               }, id="ccsd  rhf ae: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "psi4",   "reference": "rhf",  "fcae": "ae", "keywords": {},                                                                                                                               }, id="ccsd  rhf ae: psi4",       marks=using("psi4_mp2qcsk")),

        pytest.param({"call": "cfour",  "reference": "rhf",  "fcae": "fc", "keywords": {"dropmo": [1], "SCF_CONV": 12, "CC_CONV": 12, "cc_program": "vcc", "print": 2},                                                  }, id="ccsd  rhf fc: cfour-vcc",  marks=using("cfour")),
        pytest.param({"call": "cfour",  "reference": "rhf",  "fcae": "fc", "keywords": {"dropmo": [1], "SCF_CONV": 12, "CC_CONV": 12, "cc_program": "ecc"},                                                              }, id="ccsd  rhf fc: cfour-ecc",  marks=using("cfour")),
        pytest.param({"call": "cfour",  "reference": "rhf",  "fcae": "fc", "keywords": {"dropmo": [1], "SCF_CONV": 12, "CC_CONV": 12, "cc_program": "ncc"},                                                              }, id="ccsd  rhf fc: cfour-ncc",  marks=using("cfour")),
      # pytest.param({"call": "cfour",  "reference": "rhf",  "fcae": "fc", "keywords": {"dropmo": 1},                                                                                                                    }, id="ccsd  rhf fc: cfour",      marks=using("cfour")),
        pytest.param({"call": "gamess", "reference": "rhf",  "fcae": "fc", "keywords": {},                                                                                                                               }, id="ccsd  rhf fc: gamess",     marks=using("gamess")),
        pytest.param({"call": "nwchem", "reference": "rhf",  "fcae": "fc", "keywords": {"qc_module": "tce", "tce__freeze": 1 },                                                                                          }, id="ccsd  rhf fc: nwchem-tce", marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "rhf",  "fcae": "fc", "keywords": {"ccsd__freeze": 1},                                                                                                              }, id="ccsd  rhf fc: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "psi4",   "reference": "rhf",  "fcae": "fc", "keywords": {"freeze_core": True},                                                                                                            }, id="ccsd  rhf fc: psi4",       marks=using("psi4_mp2qcsk")),

        # "cfour_occupation": [[3, 1, 1, 0], [3, 0, 1, 0]]
        pytest.param({"call": "cfour",  "reference": "uhf",  "fcae": "ae", "keywords": {"REFerence": "UHF", "SCF_CONV": 12, "CC_CONV": 12, "cc_program": "vcc", "print": 2},                                             }, id="ccsd  uhf ae: cfour-vcc",  marks=using("cfour")),
        pytest.param({"call": "cfour",  "reference": "uhf",  "fcae": "ae", "keywords": {"REFerence": "UHF", "SCF_CONV": 12, "CC_CONV": 12, "cc_program": "ecc"},                                                         }, id="ccsd  uhf ae: cfour-ecc",  marks=using("cfour")),
      # pytest.param({"call": "cfour",  "reference": "uhf",  "fcae": "ae", "keywords": {"reference": "uhf"},                                                                                                             }, id="ccsd  uhf ae: cfour",      marks=using("cfour")),
        pytest.param({"call": "gamess", "reference": "uhf",  "fcae": "ae", "keywords": {"contrl__scftyp": "uhf", "ccinp__ncore": 0},                                                                        "error": _q2,}, id="ccsd  uhf ae: gamess",     marks=using("gamess")),
        pytest.param({"call": "nwchem", "reference": "uhf",  "fcae": "ae", "keywords": {"qc_module": "tce", "scf__uhf": True},                                                                                           }, id="ccsd  uhf ae: nwchem-tce", marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "uhf",  "fcae": "ae", "keywords": {"scf__uhf": True},                                                                                                  "error": _q3,}, id="ccsd  uhf ae: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "psi4",   "reference": "uhf",  "fcae": "ae", "keywords": {"reference": "uhf"},                                                                                                             }, id="ccsd  uhf ae: psi4",       marks=using("psi4_mp2qcsk")),

        pytest.param({"call": "cfour",  "reference": "uhf",  "fcae": "fc", "keywords": {"dropmo": [1], "REFerence": "UHF", "SCF_CONV": 12, "CC_CONV": 12, "cc_program": "vcc", "print": 2},                              }, id="ccsd  uhf fc: cfour-vcc",  marks=using("cfour")),
        pytest.param({"call": "cfour",  "reference": "uhf",  "fcae": "fc", "keywords": {"dropmo": [1], "REFerence": "UHF", "SCF_CONV": 12, "CC_CONV": 12, "cc_program": "ecc"},                                          }, id="ccsd  uhf fc: cfour-ecc",  marks=using("cfour")),
      # pytest.param({"call": "cfour",  "reference": "uhf",  "fcae": "fc", "keywords": {"dropmo": 1, "reference": "uhf"},                                                                                                }, id="ccsd  uhf fc: cfour",      marks=using("cfour")),
        pytest.param({"call": "gamess", "reference": "uhf",  "fcae": "fc", "keywords": {"contrl__scftyp": "uhf"},                                                                                           "error": _q2,}, id="ccsd  uhf fc: gamess",     marks=using("gamess")),
        pytest.param({"call": "nwchem", "reference": "uhf",  "fcae": "fc", "keywords": {"tce__freeze": 1, "qc_module": "tce", "scf__uhf": True},                                                                         }, id="ccsd  uhf fc: nwchem-tce", marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "uhf",  "fcae": "fc", "keywords": {"ccsd__freeze": 1, "scf__uhf": True},                                                                               "error": _q3,}, id="ccsd  uhf fc: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "psi4",   "reference": "uhf",  "fcae": "fc", "keywords": {"freeze_core": True, "reference": "uhf"},                                                                                        }, id="ccsd  uhf fc: psi4",       marks=using("psi4_mp2qcsk")),

        pytest.param({"call": "cfour",  "reference": "rohf", "fcae": "ae", "keywords": {"REFerence": "roHF", "SCF_CONV": 12, "CC_CONV": 12, "cc_program": "vcc", "print": 2},                                            }, id="ccsd rohf ae: cfour-vcc",  marks=using("cfour")),
        pytest.param({"call": "cfour",  "reference": "rohf", "fcae": "ae", "keywords": {"REFerence": "roHF", "SCF_CONV": 12, "CC_CONV": 12, "cc_program": "ecc"},                                                        }, id="ccsd rohf ae: cfour-ecc",  marks=using("cfour")),
      # pytest.param({"call": "cfour",  "reference": "rohf", "fcae": "ae", "keywords": {"reference": "rohf"},                                                                                                            }, id="ccsd rohf ae: cfour",      marks=using("cfour")),
        pytest.param({"call": "gamess", "reference": "rohf", "fcae": "ae", "keywords": {"contrl__scftyp": "rohf", "ccinp__ncore": 0, "ccinp__maxcc": 50},                                                                }, id="ccsd rohf ae: gamess",     marks=using("gamess")),
        pytest.param({"call": "nwchem", "reference": "rohf", "fcae": "ae", "keywords": {"qc_module": "tce", "scf__rohf": True},                                                                                          }, id="ccsd rohf ae: nwchem-tce", marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "rohf", "fcae": "ae", "keywords": {"scf__rohf": True},                                                                                                 "error": _q3,}, id="ccsd rohf ae: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "psi4",   "reference": "rohf", "fcae": "ae", "keywords": {"reference": "rohf", "qc_module": "ccenergy"},                                                                                   }, id="ccsd rohf ae: psi4",       marks=using("psi4_mp2qcsk")),  # TODO another way for ccenergy? (fc, too)

        pytest.param({"call": "cfour",  "reference": "rohf", "fcae": "fc", "keywords": {"dropmo": [1], "REFerence": "roHF", "SCF_CONV": 12, "CC_CONV": 12, "orbitals": 0, "cc_program": "vcc", "print": 2},              }, id="ccsd rohf fc: cfour-vcc",  marks=using("cfour")),
        pytest.param({"call": "cfour",  "reference": "rohf", "fcae": "fc", "keywords": {"dropmo": [1], "REFerence": "roHF", "SCF_CONV": 12, "CC_CONV": 12, "orbitals": 0, "cc_program": "ecc"},                          }, id="ccsd rohf fc: cfour-ecc",  marks=using("cfour")),
      # pytest.param({"call": "cfour",  "reference": "rohf", "fcae": "fc", "keywords": {"dropmo": 1, "reference": "rohf", "orbitals": 0},                                                                                }, id="ccsd rohf fc: cfour",      marks=using("cfour")),
        pytest.param({"call": "gamess", "reference": "rohf", "fcae": "fc", "keywords": {"contrl__scftyp": "rohf", "ccinp__iconv": 9, "scf__conv": 9},                                                       "wrong": _w2,}, id="ccsd rohf fc: gamess",     marks=using("gamess")),
        pytest.param({"call": "nwchem", "reference": "rohf", "fcae": "fc", "keywords": {"tce__freeze": 1, "qc_module": "tce", "scf__rohf": True},                                                                        }, id="ccsd rohf fc: nwchem-tce", marks=using("nwchem")),
        pytest.param({"call": "nwchem", "reference": "rohf", "fcae": "fc", "keywords": {"ccsd__freeze": 1, "scf__rohf": True},                                                                              "error": _q3,}, id="ccsd rohf fc: nwchem",     marks=using("nwchem")),
        pytest.param({"call": "psi4",   "reference": "rohf", "fcae": "fc", "keywords": {"e_convergence": 8, "r_convergence": 7, "freeze_core": True, "reference": "rohf", "qc_module": "ccenergy"},                      }, id="ccsd rohf fc: psi4",       marks=using("psi4_mp2qcsk")),
        # yapf: enable
    ],
)
def test_ccsd_energy_module(inp, dertype, basis, subjects, clsd_open_pmols, request):
    method = "ccsd"
    qcprog = inp["call"]
    tnm = request.node.name
    subject = clsd_open_pmols[subjects[std_refs.index(inp["reference"])]]

    inpcopy = {k: v for k, v in inp.items()}
    inpcopy["keywords"] = {
        k: (_trans_key(qcprog, basis, k) if v == "<>" else v) for k, v in inpcopy["keywords"].items()
    }

    inpcopy["driver"] = "energy"
    if not any([k.lower() in _basis_keywords for k in inpcopy["keywords"]]):
        inpcopy["basis"], basis_extras = _trans_key(qcprog, basis, "qcng_basis")
        inpcopy["keywords"].update(basis_extras)
    inpcopy["scf_type"] = "pk"
    inpcopy["corl_type"] = "conv"
    inpcopy["qc_module"] = "-".join(
        [
            qcprog,
            inp["keywords"].get(
                "qc_module", inp["keywords"].get("cfour_cc_program", inp["keywords"].get("cc_program", ""))
            ),
        ]
    ).strip("-")
    print("INP", inpcopy)

    runner_asserter(inpcopy, subject, method, basis, tnm)


###################

# Notes from test_sp_mp2_rhf_full
# TODO Molpro has frozen-core on by default. For this to pass need keyword frozen_core = False
# pytest.param('molpro', 'aug-cc-pvdz', {}, marks=using("molpro")),

# Notes from test_sp_mp2_uhf_fc
# TODO Molpro needs a new keyword for unrestricted MP2 (otherwise RMP2 by default) and needs symmetry c1
# pytest.param('molpro', 'aug-cc-pvdz', {"reference": "unrestricted"}, marks=using("molpro")),

# Notes from sp_ccsd_rhf_ull
# pytest.param("qchem", "aug-cc-pvdz", {"N_FROZEN_CORE": 0}, marks=using("qchem")),
# TODO Molpro has frozen-core on by default. For this to pass need new keyword frozen_core = False
# pytest.param('molpro', 'aug-cc-pvdz', {}, marks=using("molpro")),

# Notes from sp_ccsd_rohf_full
# pytest.param("qchem", "AUG-CC-PVDZ", {"UNRESTRICTED": False}, marks=using("qchem")),
# TODO Molpro has frozen-core on by default. For this to pass need new keyword frozen_core = False
# pytest.param('molpro', 'aug-cc-pvdz', {}, marks=using("molpro")),


# def test_sp_ccsd_rohf_ae(method, basis, keywords, nh2):
#
#    # mp2 terms (only printed for c4)
#
##    cfour isn't splitting out the singles from OS. and psi4 isn't incl the singles in either so SS + OS != corl
##    and maybe singles moved from SS to OS in Cfour btwn 2010 and 2014 versions (change in ref)
##    if not (method in ['gms-ccsd', 'nwc-ccsd']):
##        'cfour_PRINT': 2
##        assert compare_values(osccsd_corl, qcdb.variable('ccsd opposite-spin correlation energy'), tnm() + ' CCSD OS corl', atol=atol)
##        assert compare_values(ssccsd_corl, qcdb.variable('ccsd same-spin correlation energy'), tnm() + ' CCSD SS corl', atol=atol)


# def test_sp_ccsd_rohf_fc(method, keywords, nh2):
#    # differing std/semicanonical
#    ## from Cfour
#    #osccsdcorl = -0.1563275
#    #ssccsdcorl = -0.0365048
#    ##ssccsdcorl = -0.036502859383024
#
#    ## from Psi4. psi & nwchem agree to 6
#    osccsd_corl = -0.152968752464362
#    ssccsd_corl = -0.036502859383024
#
#    ## from gamess.
#    #ccsdcorl = -0.1928447371
#    #ccsdtot = -55.7775819971
#    # from Cfour
#
#    scf_tot = -55.5847372600528120
#    mp2_tot = -55.760613403041812
#    ccsd_tot = -55.7775634749542241
#
#    # gms CCSD correlation disagrees with Cfour, Psi4, and NWChem by ~2.e-4
#    # hf is in agreement across all programs
#    if method.startswith('gms'):
#        atol = 2.e-5
