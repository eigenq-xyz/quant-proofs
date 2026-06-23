-- Research pipeline: formal no-look-ahead guarantee for the backtesting stage.
-- Central claim: signals consumed by the backtester cannot use future information.
-- `NoLookahead` states the finite, pointwise non-anticipation property; `Measurability`
-- upgrades it to genuine 𝓕ₜ-measurability (adaptedness to the natural filtration of the
-- price process), citing `ftap-proofs`. `Bridge` connects the two: measure-theoretic
-- adaptedness implies the pointwise property, so the two are one guarantee, not two.

import ResearchPipeline.NoLookahead
import ResearchPipeline.NoLeakage
import ResearchPipeline.Measurability
import ResearchPipeline.Bridge

namespace ResearchPipeline

end ResearchPipeline
