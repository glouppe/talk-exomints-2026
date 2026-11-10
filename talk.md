class: black-slide
background-image: url(figures/title-bg.jpg)
background-size: cover

.overlay-box.overlay-title-slide[
.overlay-title[Simulation-based inference for exoplanets]

.title-author[![](figures/faces/gilles.jpg).title-author-text[Gilles Louppe<br>.smaller[[g.louppe@uliege.be](mailto:g.louppe@uliege.be)]]]

.title-author[![](figures/faces/maxdax.jpg).title-author-text[Max Dax<br>.smaller[[maximilian.dax@tuebingen.mpg.de](mailto:maximilian.dax@tuebingen.mpg.de)]]]

.title-footer[.smaller[Exomints 2026<br>November 10, 2026]<span style="display: flex; align-items: flex-end; gap: 0.8em; margin-left: 1em;"><img src="figures/logo-ellis-white.png" style="height: 1em; margin-bottom: 0.2em;"><img src="figures/logo-uliege-white.png" style="height: 1.5em;"></span>]
]

.footnote[Illustration of WASP-39 b: NASA, ESA, CSA, J. Olmsted (STScI).]

???

Thank you for having us.

The whole tutorial rests on one idea. If you can simulate your data, you can infer the parameters that produced them, without the likelihood.

For retrievals, this buys three things. Realistic simulators. Expensive physics, run once and in parallel. And results we can actually check.

---

class: black-slide
background-image: url(figures/ocean-x.jpg)
background-size: cover

.overlay-box.overlay-top-left[
.overlay-title[Ocean currents]

.italic[Observations:] the height $x$ of the sea surface, measured coarsely by satellite altimeters, along their tracks.
]

.footnote[Sea surface height anomaly, Gulf Stream off North Carolina, January 21, 2023, from 7 altimeters. Credit: NASA/JPL-Caltech/Copernicus Marine Service ([PIA25773](https://science.nasa.gov/photojournal/sea-level-visualization-of-gulf-stream)).]

???

Let's start far from exoplanets, with the ocean. From space, altimeters measure the height of the sea surface. Here, the Gulf Stream off North Carolina. This is our observation, $x$.

---

class: black-slide

.bg-video[<video autoplay muted loop playsinline poster="figures/ocean-z-poster.jpg" src="figures/videos/ocean-z.mp4"></video>]

.overlay-box.overlay-top-left[
.overlay-title[Ocean currents]

.italic[Latent states:] the currents $z$ that shape the surface, the Gulf Stream, its jets and eddies.
]

.footnote[Perpetual Ocean, ECCO2 model. Visualization: NASA/Goddard Space Flight Center Scientific Visualization Studio ([SVS 3827](https://svs.gsfc.nasa.gov/3827)).]

???

What shapes this surface are the currents, with their meanders and eddies. That's the hidden state, $z$. Many different oceans fit the same coarse picture.

---

class: black-slide

.bg-video[<video autoplay muted loop playsinline poster="figures/ocean-theta-poster.jpg" src="figures/videos/ocean-theta.mp4"></video>]

.overlay-box.overlay-top-left[
.overlay-title[Ocean currents]

.italic[Parameters:] the global constants $\theta$ of the ocean model, such as its viscosity $\nu$.
]

.footnote[Illustration: 2D turbulence on a $\beta$-plane, same forcing, three viscosities; current speed.]

???

The currents follow known equations, but their constants are poorly known, like the viscosity. Those are the parameters, $\theta$. Three viscosities, three different oceans.

This structure shows up whenever an instrument sits between us and what we study.

---

class: black-slide

.bg-video[<video autoplay muted loop playsinline poster="figures/gw-x-poster.jpg?v=2" src="figures/videos/gw-x.mp4?v=2"></video>]

.overlay-box.overlay-top-left[
.overlay-title[Gravitational waves]

.italic[Observations:] the strain $x$ recorded by LIGO. In time and frequency, a chirp rises out of the noise.
]

.footnote[Data: LIGO Hanford, GW150914, September 14, 2015 ([GWOSC](https://gwosc.org/events/GW150914/)). Whitened strain, band-passed 35–350 Hz (white), and its wavelet transform, 20–512 Hz.]

???

Second example, gravitational waves. This is what LIGO recorded in September 2015. Mostly noise, and then a chirp, a fraction of a second long. That's $x$.

---

class: black-slide

.bg-video[<video autoplay muted loop playsinline poster="figures/gw-z-poster.jpg" src="figures/videos/gw-z.mp4"></video>]

.overlay-box.overlay-top-left[
.overlay-title[Gravitational waves]

.italic[Latent states:] the signal $z$ of two black holes that spiral into each other, merge, and ripple space-time.
]

.footnote[Simulation: B. J. Kelly, C. Henze, T. Sandstrom, [NASA SVS 13197](https://svs.gsfc.nasa.gov/13197).]

???

The chirp comes from two black holes merging. General relativity predicts the waveform. That's $z$.

---

class: black-slide
background-image: url(figures/gw-theta.jpg)
background-size: cover

.overlay-box.overlay-top-left[
.overlay-title[Gravitational waves]

.italic[Parameters:] the properties $\theta$ of the binary, masses, spins, distance, orientation, sky position (15 in total).
]

.footnote[Illustration: LIGO/Caltech/MIT/Sonoma State (Aurore Simonnet).]

???

The waveform depends on the masses, the spins, the distance and the orientation, fifteen numbers in all. That's $\theta$.

---

class: black-slide

.bg-video[<video autoplay muted loop playsinline poster="figures/exo-x-poster.jpg" src="figures/videos/exo-x.mp4"></video>]

.overlay-box.overlay-top-right.exo-spectrum[
![](figures/exo-x-spectrum.png)
]

.overlay-box.overlay-intro[
.overlay-title[Exoplanets]

.italic[Observations:] the spectrum $x$ of a planet, whose light direct imaging separates from its star.
]

.footnote[HR 8799, Keck, 2009–2016: Jason Wang (Caltech), Christian Marois (NRC Herzberg), [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). Spectrum: simulated benchmark of [Vasist et al](https://arxiv.org/abs/2301.06575), A&A 2023.]

???

And exoplanets. Four planets around HR 8799, imaged over seven years. Spread the light of one planet, and you get a spectrum. That's $x$.

---

class: black-slide
background-image: url(figures/exo-z.jpg?v=6)
background-size: cover

.overlay-box.overlay-intro[
.overlay-title[Exoplanets]

.italic[Latent states:] the atmosphere $z$, its temperature profile, its molecules, its clouds.
]

.footnote[VHS 1256 b. Illustration: NASA, ESA, CSA, Joseph Olmsted (STScI).]

???

The spectrum comes from the atmosphere, its temperature, its molecules, its clouds. Here, silicate clouds seen by JWST. That's $z$.

---

class: black-slide
background-image: url(figures/exo-theta.jpg?v=2)
background-size: cover

.overlay-box.overlay-intro[
.overlay-title[Exoplanets]

.italic[Parameters:] the bulk properties $\theta$, C/O, metallicity, gravity, radius, clouds, mixing.
]

.footnote[Ten hot Jupiters studied with Hubble ([Sing et al](https://doi.org/10.1038/nature16068), Nature 2016). Illustration: ESA/Hubble & NASA.]

???

And the atmosphere follows from a few bulk parameters, like the C/O ratio, the metallicity or the gravity. They tell us how the planet formed. That's $\theta$.

---

class: middle

.center.width-80[![](figures/setup.svg)]

## Inverse problems in science

Given an observation $x$, estimate the posterior distribution
$$p(\theta | x) = \frac{p(x|\theta) p(\theta)}{p(x)}, \quad \text{with} \quad p(x | \theta) = \int p(x | z) p(z | \theta) \text{d}z,$$
of the parameters $\theta$, with the latent states $z$ integrated out.

???

Three examples, one structure. Parameters set the physics, the physics produces a state, an instrument records it.

We want the posterior. The catch is the likelihood, which integrates over every hidden state. We can simulate it, but we can't evaluate it.

---

class: middle

.grid[
.kol-1-4[&nbsp;]
.kol-3-4[.flow.flow-right[Generation]]
]

.grid[
.kol-1-4[&nbsp;]
.kol-1-4[.center[.icons[![](figures/icons/des-questions.png)]<br>.bold[Prior] $p(\theta)$]]
.kol-1-4[.center[.icons[![](figures/icons/galaxie.png)![](figures/icons/exoplanet.png)]<br>.bold[Physics] $p(z | \theta)$]]
.kol-1-4[.center[.icons[![](figures/icons/observatoire.png)![](figures/icons/satellite.png)]<br>.bold[Instrument] $p(x | z)$]]
]

.recipe[
.grid[
.kol-1-4[.italic[Ocean currents]]
.kol-1-4[.center[viscosity, mixing, drag]]
.kol-1-4[.center[Navier–Stokes]]
.kol-1-4[.center[altimetry, noise]]
]
.grid[
.kol-1-4[.italic[Gravitational waves]]
.kol-1-4[.center[masses, spins, distance]]
.kol-1-4[.center[general relativity]]
.kol-1-4[.center[detector response, noise]]
]
.grid[
.kol-1-4[.italic[Exoplanets]]
.kol-1-4[.center[C/O, metallicity, clouds]]
.kol-1-4[.center[radiative transfer]]
.kol-1-4[.center[spectrograph, noise]]
]
]

.grid[
.kol-1-4[&nbsp;]
.kol-3-4[.flow.flow-left[Inference]]
]

???

Generation goes left to right, through the prior, the physics and the instrument. Inference goes back, from right to left.

---

class: middle

## A minimal exoplanet simulator

Prior, $\theta \sim p(\theta)$: six parameters, each uniform over a range.

.center[
<video poster="figures/toy-walk-1.png" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-walk-1.mp4" type="video/mp4">
</video>
]

???

To make this concrete, here is a small simulator that we'll use throughout. It's a toy, but it has the structure of a real retrieval code. Six parameters, drawn uniformly from the prior.

---

class: middle

## A minimal exoplanet simulator

Physics, $z \sim p(z | \theta)$ or $z = g(\theta)$: temperature, chemistry, clouds.

.center[
<video poster="figures/toy-walk-2.png" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-walk-2.mp4" type="video/mp4">
</video>
]

???

The physics gives the atmosphere. A temperature profile, water, methane, carbon monoxide, and a cloud deck. Watch methane appear where it gets cool.

The physics can be random or not. Patchy clouds that change between visits are random, so $z$ is drawn from $p(z | \theta)$. Our toy, like most retrievals today, is deterministic, so $z = g(\theta)$.

---

class: middle

## A minimal exoplanet simulator

Radiative transfer: the light $f(\theta)$ that the atmosphere emits.

.center[
<video poster="figures/toy-walk-3.png" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-walk-3.mp4" type="video/mp4">
</video>
]

???

Radiative transfer gives the light. The dips are absorption bands. The peaks are windows into deeper, hotter layers.

---

class: middle

## A minimal exoplanet simulator

Instrument, $x \sim p(x | z)$: binned, with noise, any noise we can simulate.

.center[
<video poster="figures/toy-walk-4.png" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-walk-4.mp4" type="video/mp4">
</video>
]

???

Finally, the instrument bins the light and adds noise. That's all we observe.

Since our physics is deterministic, the noise is the only randomness. So in this toy we do have a likelihood, and we can check against MCMC later.

Running this forward is easy. The question is how to go back.

---

class: middle

## Prior predictive check

Before seeing any data, we check the .bold[forward model] against domain knowledge: we draw $\theta \sim p(\theta)$, simulate, and compare summary statistics with known objects.

.center[
<video poster="figures/toy-prior-pc.png?v=3" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-prior-pc.mp4?v=3" type="video/mp4">
</video>
]

???

Before touching any data, we check the simulator. We draw from the prior and look at a number we know from real objects, the J − K colour.

Our toy fails. 42% of the draws are redder than anything known. In a real analysis, we would fix the prior or the physics now.

And we never use the observation for this. That would be using the data twice.

---

class: black-slide

.bg-video[<video autoplay muted loop playsinline poster="figures/galaxy-1.jpg?v=6" src="figures/videos/galaxy-1.mp4?v=6"></video>]

.overlay-box.overlay-bottom-left.narrow-box[
.overlay-title[Inference algorithms]

Estimating $p(\theta | x)$: classical methods in blue, simulation-based inference in pink.
]

???

How do we go back? There are many algorithms. In blue, the classics, MCMC, nested sampling, ABC. In pink, simulation-based inference with neural networks.

---

count: false
class: black-slide

.bg-video[<video autoplay muted playsinline poster="figures/galaxy-2.jpg?v=6" src="figures/videos/galaxy-2.mp4?v=6"></video>]

.overlay-box.overlay-bottom-left.narrow-box[
.overlay-title[Inference algorithms]

Estimating $p(\theta | x)$: classical methods in blue, simulation-based inference in pink.
]

???

Today, two of them. Neural posterior estimation, and its flow-matching cousin. NPE is the simplest, and the most used for exoplanets.

---

class: middle

## Neural posterior estimation

We train a conditional density estimator $q\_\phi(\theta | x)$, typically a .bold[normalizing flow], to approximate the posterior of .bold[any] observation $x$,
$$\phi^\star = \arg\min\_\phi \; \mathbb{E}\_{p(\theta)} \mathbb{E}\_{p(x | \theta)} \left[ -\log q\_\phi(\theta | x) \right].$$

The parameters are drawn from the prior and the observations from the simulator, so that the likelihood is sampled, never evaluated.

Up to a constant, this loss is the expected divergence to the true posterior,
$$\mathbb{E}\_{p(x)} \, \text{KL}\big( p(\theta|x) \, \Vert \, q\_\phi(\theta|x) \big).$$

???

The idea of NPE is simple. Train a network that takes a spectrum and returns a distribution over the parameters.

The training pairs come from the simulator. The minimum of this loss is the true posterior. And we never evaluate a likelihood.

---

class: middle

.center[
<video poster="figures/npe-pipeline.png" muted loop autoplay playsinline class="anim" style="width: 100%;">
<source src="figures/videos/npe-pipeline.mp4" type="video/mp4">
</video>
]

By the change of variables, the density is exact,
$$\log q\_\phi(\theta | x) = \log \mathcal{N}(t\_3 \circ t\_2 \circ t\_1(\theta); 0, I) + \sum\_{k=1}^{3} \log \left| \det J\_{t\_k} \right|.$$

???

The network has two parts. An embedding network summarizes the spectrum. A normalizing flow turns these features into a density over the parameters.

The flow is an invertible map to a Gaussian, so the density is exact. Watch real samples become Gaussian, layer by layer.

---

class: middle

## Embedding network

The embedding network compresses the spectrum into a few features $h(x)$, which condition the flow. Its architecture is a .bold[choice], adapted to the data. For our 94 bins, we use a multilayer perceptron, a stack of layers $z\_{l+1} = \sigma(W\_l\, z\_l + b\_l)$.

.center[
<video poster="figures/toy-embedding-arch.png?v=2" muted loop autoplay playsinline class="anim" style="width: 100%;">
<source src="figures/videos/toy-embedding.mp4" type="video/mp4">
</video>
]

The embedding is trained jointly with the flow, by the same loss.

???

Let's open the embedding. It's a stack of simple layers, here a plain multilayer perceptron, because our spectra are short.

That's a choice. Longer or messier data would call for convolutions or transformers.

Nobody tells it where the molecules absorb. It learns that from the simulations.

---

class: middle

## Training

We simulate $N$ pairs $(\theta\_i, x\_i) \sim p(\theta, x)$ and minimize the empirical estimate of the loss,
$$L(\phi) = \mathbb{E}\_{p(\theta, x)} \left[ -\log q\_\phi(\theta | x) \right] \approx \frac{1}{N} \sum\_{i=1}^{N} -\log q\_\phi(\theta\_i | x\_i),$$
with the noise added on the fly. The simulations run in parallel, once.

.center[
<video poster="figures/toy-training.png" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-training.mp4" type="video/mp4">
</video>
]

???

The training data is just simulations. Half a million here, half an hour on a laptop. With petitRADTRANS, twelve million spectra took about 17,000 CPU hours. That cost is paid once, in parallel.

Then, plain gradient descent, with fresh noise at every epoch.

---

class: middle

## Amortization

Once trained, the network gives the posterior of any new spectrum in a fraction of a second. Testing it on thousands of spectra becomes affordable.

.center[
<video poster="figures/toy-gallery.png?v=3" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-gallery.mp4?v=3" type="video/mp4">
</video>
]

???

Here's the payoff. Once trained, every new spectrum gets its posterior instantly. Ten planets in a couple of seconds, against an hour and a half with MCMC.

And because it's cheap, we can afford to test it.

---

class: middle

## Results on the toy problem

Consider an observed spectrum $x\_{\rm obs}$, simulated from known parameters $\theta^\star$ hidden from the methods.

.center.width-100[![](figures/toy-xobs.png)]

???

Now, one observed spectrum. We simulated it ourselves, so we know the answer.

---

class: middle

.center.width-65[![](figures/toy-corner.png)]

???

NPE in red, MCMC in grey, nested sampling in orange. They agree, and they contain the truth.

NPE took two seconds. MCMC, nine minutes. Nested sampling, an hour.

---

class: middle

## Calibration

A posterior is .bold[calibrated] if its 90% credible regions contain the true parameters 90% of the time, and likewise at every level.

.center[
<video poster="figures/toy-coverage.png?v=2" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-coverage.mp4?v=2" type="video/mp4">
</video>
]

Coverage is necessary but not sufficient, since the prior itself is calibrated. TARP, MIRA and L-C2ST are stronger tests.

.footnote[TARP: [Lemos et al](https://arxiv.org/abs/2302.03026), ICML 2023. MIRA: [Sharief et al](https://arxiv.org/abs/2605.02014), ICML 2026. L-C2ST: [Linhart et al](https://arxiv.org/abs/2306.03580), NeurIPS 2023.]

???

But can we trust it? We check calibration, on a thousand simulated spectra.

On the left, 90% intervals. They should catch the truth 90% of the time. On the right, the same at every level. The grey bands show what chance allows, and we stay inside them.

This took a minute. With MCMC, a week.

---

class: middle

.avatars[![](figures/faces/arnaud.jpg)![](figures/faces/joeri.png)![](figures/faces/frozet.jpg)![](figures/faces/gilles.jpg)]

Neural posteriors can be .bold[overconfident], even when trained as recommended. Balancing the training makes them conservative, which is preferable for science.

.grid[
.kol-1-2[.center.width-100[![](figures/coverage-crisis.png)]]
.kol-1-2[.center.width-100[![](figures/balancing.png)]]
]
.grid[
.kol-1-2[.center[Coverage of common SBI algorithms]]
.kol-1-2[.center[Balanced NPE (last column)]]
]

.footnote[[Hermans et al](https://arxiv.org/abs/2110.06581), TMLR 2022. [Delaunoy et al](https://arxiv.org/abs/2304.10978), 2023. See also [Falkiewicz et al](https://arxiv.org/abs/2310.13402), NeurIPS 2023.]

???

Calibration is not a formality. In a benchmark, many SBI methods were overconfident, even when trained as recommended. Balanced NPE pushes them to the safe side.

---

class: middle

## Posterior predictive check

To check the .bold[forward model], we draw $\theta \sim q\_\phi(\theta | x\_{\rm obs})$, simulate, and compare with the observation.

.center[
<video poster="figures/toy-ppc.png" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-ppc.mp4" type="video/mp4">
</video>
]

???

Calibration tests the network. It says nothing about the simulator. For that, we simulate from the posterior and compare with the data. Here, it covers the data within the noise.

---

class: middle

## When the model is wrong

.center.width-100[![](figures/toy-misspec-obs.png)]

Consider now a new observation of the same planet, with an absorption band at 1.52 μm that the simulator does not have.

???

Now, let's break the simulator. Same planet, but with an absorption band that our simulator doesn't have. Think of ammonia.

---

class: middle

.center.width-100[![](figures/toy-misspec.png?v=2)]

.center[The posteriors are .bold[confident and exact, but wrong], because of misspecification.]

.footnote[Detecting and handling misspecification: [Schmitt et al](https://arxiv.org/abs/2112.08866), 2023; [Ward et al](https://arxiv.org/abs/2210.06564), NeurIPS 2022.]

???

All three methods agree. They're tight. And they're all wrong. MCMC is exact, but for the wrong model.

Calibration can't see this. The residuals can. Two points at five to six sigma, right at the band. The fix is in the model.

---

class: middle

.avatars[![](figures/faces/malavika.jpg)![](figures/faces/frozet.jpg)![](figures/faces/absil.jpg)![](figures/faces/molliere.jpg)![](figures/faces/nasedkin.jpg)![](figures/faces/gilles.jpg)]

<br>

.center.width-85[![](figures/vasist23-header.png)]

.grid[
.kol-3-5[.center.width-90[![](figures/vasist23-corner.png)]]
.kol-2-5[
.center.width-65[![](figures/vasist23-ppc.png)]
.center.width-65[![](figures/vasist23-coverage.png)]
]
]

.footnote[[Vasist et al](https://arxiv.org/abs/2301.06575), A&A 672, A147, 2023. Simulated benchmark spectrum.]

???

Does this work at scale? Our 2023 paper did it with petitRADTRANS, sixteen parameters and twelve million simulations. NPE matches MultiNest, and passes both checks.

---

class: middle

.avatars[![](figures/faces/malavika.jpg)![](figures/faces/molliere.jpg)![](figures/faces/absil.jpg)![](figures/faces/gilles.jpg)![](figures/faces/more.png)]

.center.width-90[![](figures/wise-header.png)]

.grid[
.kol-3-5[<br>.center.width-100[![](figures/wise-spectra.png)]]
.kol-2-5[.center.width-100[![](figures/wise-posterior.png)]]
]

.footnote[[Vasist et al](https://arxiv.org/abs/2507.12264), A&A 703, A70, 2025. Real data: JWST/MIRI, HST/WFC3, Gemini/GNIRS.]

???

And on real data. WISE 1738, a brown dwarf at 400 kelvin, with JWST, HST and Gemini. NPE finds water, methane, ammonia, and signs of vertical mixing. Everything passed the diagnostics.

---

class: middle

## Beyond normalizing flows

A continuous flow replaces the chain of invertible transformations by a vector field, given by an unconstrained network. It is more flexible and scales better to .bold[high-dimensional] parameter spaces.

.grid[
.kol-1-2[.center.width-100[![](figures/gebhard-dnf.png)]]
.kol-1-2[.center.width-100[![](figures/gebhard-cnf.png)]]
]
.grid[
.kol-1-2[.center[Discrete flow (NPE)]]
.kol-1-2[.center[Continuous flow (FMPE)]]
]

.footnote[Credits: [Gebhard et al](https://arxiv.org/abs/2410.21477), A&A 2025.]

???

The flow is only one choice. A continuous flow replaces the chain of transformations by a vector field. It's more flexible, and it scales better with many parameters.

---

class: middle

## Flow matching posterior estimation (FMPE)

.center[
<video poster="figures/fm-flow.png?v=2" muted loop autoplay playsinline class="anim" style="width: 80%;">
<source src="figures/videos/fm-flow.mp4?v=2" type="video/mp4">
</video>
]

<br>

<div class="center">Noise $\theta_0 \sim \mathcal{N}(0, I)$ flows along a vector field $v_\phi(\theta_t, t; x)$, from $t = 0$ to $t = 1$, where it follows the posterior $q_\phi(\theta | x)$.</div>

.footnote[Animation: the exact flow-matching vector field towards a two-mode target.]

???

Picture samples flowing from noise to the posterior. Sampling means solving an ODE.

---

class: middle

As for discrete flows, the density is exact,
$$\begin{aligned} \log q\_\phi(\theta | x) &= \log \mathcal{N}(\theta\_0; 0, I) + \int\_1^0 \text{tr} \left( \frac{\partial v\_\phi(\theta\_t, t; x)}{\partial \theta\_t} \right) dt \\\\ &= \log \mathcal{N}(\theta\_0; 0, I) + \int\_1^0 \nabla \cdot v\_\phi(\theta\_t, t; x) \, dt, \end{aligned}$$
where $\theta\_0$ is the noise that $\theta$ flows back to at $t = 0$. The vector field is trained by regression along straight paths $\theta\_t = (1-t)\, \theta\_0 + t\, \theta$,
$$\min\_\phi \; \mathbb{E}\_{t \sim \mathcal{U}(0,1),\; \theta\_0 \sim \mathcal{N}(0, I),\; (\theta, x) \sim p(\theta, x)} \left[ \left\Vert v\_\phi(\theta\_t, t; x) - (\theta - \theta\_0) \right\Vert^2 \right],$$
which requires no integration of the flow.

.footnote[[Dax et al](https://arxiv.org/abs/2305.17161), NeurIPS 2023.]

???

The density is still exact. Same idea as before, with tiny steps. The sum of log-determinants becomes an integral of a trace.

And training is plain regression. Point along straight lines, from noise to parameters.

---

class: middle

.avatars[![](figures/faces/gebhard.jpg)![](figures/faces/wildberger.jpg)![](figures/faces/maxdax.jpg)![](figures/faces/kofler.jpg)![](figures/faces/more.png)]

<br>

.center.width-85[![](figures/gebhard-header.png)]

.grid[
.kol-1-2[.center.width-90[![](figures/gebhard-corner.png)]]
.kol-1-2[.center.width-90[![](figures/gebhard-efficiency.png)]]
]

.footnote[[Gebhard et al](https://arxiv.org/abs/2410.21477), A&A 2025. Simulated benchmark of Vasist et al.]

???

Max and colleagues applied this to the same benchmark. One network for any noise level. And importance sampling on top, which brings us to the next slide.

---

class: middle

## Cheat code: importance sampling

When the likelihood can be evaluated, the network becomes a .bold[proposal]. Samples $\theta\_i \sim q\_\phi(\theta|x)$, weighted by
$$w\_i = \frac{p(x | \theta\_i) \, p(\theta\_i)}{q\_\phi(\theta\_i | x)},$$
follow the .bold[exact] posterior.

.center[
<video poster="figures/toy-is.png" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-is.mp4" type="video/mp4">
</video>
]

???

Here's a cheat code. If you can evaluate the likelihood, even slowly, the network becomes a proposal. Sample, weight, resample, and you land on MCMC.

As a bonus, the average weight is the evidence. A few thousand likelihood calls, not millions.

---

class: middle

.center.width-70[![](figures/toy-is-corner.png)]

.center[With importance sampling (blue), NPE matches MCMC (grey).]

???

All six parameters. Red is the network alone, blue after reweighting, grey is MCMC. Blue and grey coincide.

---

class: middle

## Model comparison

We compare two simulators, with and without a cloud deck. By eye, both fit.

.center.width-100[![](figures/mc-ppc.png)]

???

Are there clouds? That's a question about models, not parameters. So, two simulators, with and without clouds.

On the cloudy planet, both fit by eye, but the evidence strongly favours clouds. On the clear one, a small penalty for the useless cloud parameter.

---

class: middle

<img src="figures/mc-bayes.png?v=2" style="display: block; margin: 0 auto; width: 46%;">

The .bold[Bayes factor] $B = p(x | \text{cloudy}) \,/\, p(x | \text{clear})$ compares the evidence of the two models.

<div class="evidence-rows">
<div><span>Nested sampling</span>$$p(x|M) \approx \sum_i p(x|\theta_i, M) \, \Delta X_i$$</div>
<div><span>Importance sampling</span>$$p(x|M) \approx \frac{1}{n} \sum_i \frac{p(x|\theta_i, M) \, p(\theta_i|M)}{q_\phi(\theta_i|x)} = \frac{1}{n} \sum_i w_i$$</div>
<div><span>Classifier</span>$$\log B \approx \log \frac{d_\psi(x)}{1 - d_\psi(x)}, \quad d_\psi(x) \approx p(\text{cloudy}|x)$$</div>
</div>

.footnote[Error bars: one standard deviation over 6 runs with new seeds. Classifier: [Radev et al](https://arxiv.org/abs/2004.10629), 2020. Model comparison without the evidence: MIRA, [Sharief et al](https://arxiv.org/abs/2605.02014), ICML 2026.]


???

The Bayes factor compares the evidences. Three ways to get it.

Nested sampling, the reference. Importance sampling, the same answer, and far more reproducible. And a classifier, with no likelihood at all, but it saturates when the evidence is overwhelming.

The error bars come from six repeated runs.

---

class: black-slide, middle

.bg-video[<video autoplay muted loop playsinline poster="figures/exo-x-poster.jpg" src="figures/videos/exo-x.mp4" style="filter: brightness(0.55);"></video>]

.punch[
.punch-title[Summary]

Inference requires a simulator, not a likelihood, so the simulator can be as realistic as needed.

A neural posterior estimator is trained once; it then gives the posterior of any spectrum in seconds, which makes validation affordable.

Calibration tests the network; posterior predictive checks test the model.

An overdispersed posterior is safer than an overconfident one.

With a likelihood, importance sampling corrects the network and gives the evidence, for model comparison.
]

???

To sum up.

You need a simulator, not a likelihood, so make it realistic. NPE is trained once, and then it's fast enough to be checked. Check the network with calibration, and the model with predictive checks.

Prefer overdispersed to overconfident. And remember, outside what it was trained on, the network still answers, silently.

---

class: middle

## Reading list

.reading[
Reviews

- Dax et al, [An introduction to Bayesian and frequentist simulation-based inference with machine learning](https://arxiv.org/abs/2607.21702), 2026.
- Cranmer, Brehmer and Louppe, [The frontier of simulation-based inference](https://arxiv.org/abs/1911.01429), PNAS 2020.
- Deistler et al, [Simulation-based inference: a practical guide](https://arxiv.org/abs/2508.12939), 2025.
- Arruda et al, [Diffusion models in simulation-based inference: a tutorial review](https://arxiv.org/abs/2512.20685), TMLR 2026.

Simulation-based inference for exoplanets

- Márquez-Neila et al, [Supervised machine learning for analysing spectra [...]](https://arxiv.org/abs/1806.03944), Nature Astronomy 2018.
- Haldemann et al, [Exoplanet characterization using conditional invertible neural networks](https://arxiv.org/abs/2202.00027), A&A 2023.
- Vasist et al, [Neural posterior estimation for exoplanetary atmospheric retrieval](https://arxiv.org/abs/2301.06575), A&A 2023.
- Aubin et al, [Simulation-based inference for exoplanet atmospheric retrieval [...]](https://arxiv.org/abs/2309.09337), 2023.
- Ardévol Martínez et al, [FlopPITy: enabling self-consistent exoplanet atmospheric retrievals [...]](https://arxiv.org/abs/2401.04168), A&A 2024.
- Gebhard et al, [Flow matching for atmospheric retrieval of exoplanets](https://arxiv.org/abs/2410.21477), A&A 2025.
- Lueber et al, [Near-instantaneous atmospheric retrievals and model comparison with FASTER](https://arxiv.org/abs/2502.18045), ApJL 2025.
- Vasist et al, [Panchromatic characterization of the Y0 brown dwarf WISE 1738 using JWST/MIRI](https://arxiv.org/abs/2507.12264), A&A 2025.
]

???

If you want to go further, start with our review with Max. The rest is for the curious.

---

class: black-slide
background-image: url(figures/title-bg.jpg)
background-size: cover

.closing-end[The end.]

???

A prior, physics, an instrument. That's a simulator. We can't evaluate the likelihood, but we can simulate, and that's enough.

Thank you.

---

count: false
class: middle

## Backup: 30-parameter retrieval

.center.width-70[![](figures/t30-corner-full.png?v=3)]

.footnote[TSNPE: truncated sequential NPE, [Deistler et al](https://arxiv.org/abs/2210.04815), NeurIPS 2022. Free retrieval, 0.8 to 5 μm.]

???

A harder version of our toy, closer to a real free retrieval. Thirty parameters: a temperature profile with ten nodes, fifteen molecules and a non-grey cloud, from 0.8 to 5 microns. Many are barely constrained, like the trace molecules. Each network gets one million simulations. TSNPE spends them in five rounds, around the observation.

Amortized NPE gets the broad picture, but it is off on the temperature and on the trace species. TSNPE trains on the observation in rounds, and each round simulates only where the posterior is. With importance sampling on top, it agrees closely with nested sampling.

One honest caveat. TSNPE puts more mass than nested sampling in a tail at low abundances, about 17% against 6%, and two independent TSNPE runs agree on it. Which one is right would need a third reference.

---

count: false
class: middle

.center.width-100[![](figures/t30-marginals.png?v=3)]

???

The same three posteriors, one parameter at a time, each over its full prior range. The molecules that shape the spectrum, like water, methane or carbon monoxide, are sharply constrained, and all methods agree. The trace molecules are upper limits, where amortized NPE drifts and TSNPE follows nested sampling.

For the barely constrained temperature ratios, the networks are close to flat, as the prior. Nested sampling is tilted. That is another hint that nested sampling struggles in thirty dimensions.

---

count: false
class: middle

.center.width-100[![](figures/t30-ppc.png?v=3)]

???

How well does each posterior fit the data? We simulate from each posterior and compare with the observation. The residuals of amortized NPE spread at short wavelengths, and its chi-square is far too high. TSNPE and nested sampling sit where the truth sits.

Importance sampling tells the same story. It works for TSNPE, and collapses for amortized NPE.

The evidence is less clear-cut. TSNPE gives a log evidence of −103.3, stable over four runs. Nested sampling gives −102.7 with 2000 live points, and −101.7 with 500. In thirty dimensions, nested sampling itself becomes hard to trust.

