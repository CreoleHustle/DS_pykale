import torch

from kale.embed.multimodal_fusion_methods import Concat, LowRankTensorFusion, MultiplicativeInteractions2Modal


def test_concat():
    concat = Concat()
    m1 = torch.randn(4, 3, 5)
    m2 = torch.randn(4, 2, 5)
    output = concat([m1, m2])
    assert output.shape == (4, 5 * (3 + 2))


def test_multiplicative_interactions():
    mi2m = MultiplicativeInteractions2Modal(input_dims=(10, 20), output_dim=30, output="vector")
    m1 = torch.randn(4, 10)
    m2 = torch.randn(4, 20)
    output = mi2m([m1, m2])
    assert output.shape == (4, 20)


def test_low_rank_tensor_fusion():
    lrtf = LowRankTensorFusion(input_dims=(3, 3, 3), output_dim=1, rank=2)
    m1 = torch.randn(4, 3)
    m2 = torch.randn(4, 3)
    m3 = torch.randn(4, 3)
    output = lrtf([m1, m2, m3])
    assert output.shape == (4, 1)
