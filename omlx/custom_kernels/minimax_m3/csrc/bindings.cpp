#include <nanobind/nanobind.h>
#include <nanobind/stl/variant.h>

#include "minimax_msa.h"

namespace nb = nanobind;
using namespace nb::literals;

NB_MODULE(_ext, m) {
  m.doc() = "Native MiniMax M3 kernels for oMLX";

  m.def(
      "minimax_msa_topk",
      &omlx::minimax_m3_kernels::minimax_msa_topk,
      "idx_queries"_a,
      "idx_keys"_a,
      "q_start"_a,
      "scale"_a,
      "block_size"_a,
      "topk"_a,
      "init_blocks"_a,
      "local_blocks"_a,
      "stream"_a = nb::none());
}
