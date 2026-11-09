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

The tutorial rests on one idea. If we can simulate the data, we can infer the parameters that produced them, without evaluating the likelihood.

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

First example, the ocean. Satellite altimeters measure the height of the sea surface along their tracks, at a resolution of tens of kilometres. Here, the Gulf Stream off North Carolina. Red is above average, blue below. This is $x$.

---

class: black-slide

.bg-video[<video autoplay muted loop playsinline poster="figures/ocean-z-poster.jpg" src="figures/videos/ocean-z.mp4"></video>]

.overlay-box.overlay-top-left[
.overlay-title[Ocean currents]

.italic[Latent states:] the currents $z$ that shape the surface, the Gulf Stream, its jets and eddies.
]

.footnote[Perpetual Ocean, ECCO2 model. Visualization: NASA/Goddard Space Flight Center Scientific Visualization Studio ([SVS 3827](https://svs.gsfc.nasa.gov/3827)).]

???

The surface height is shaped by the currents, the Gulf Stream, its meanders and its eddies. This is $z$. Many states of the ocean fit the same coarse heights, so we want a distribution over them.

---

class: black-slide

.bg-video[<video autoplay muted loop playsinline poster="figures/ocean-theta-poster.jpg" src="figures/videos/ocean-theta.mp4"></video>]

.overlay-box.overlay-top-left[
.overlay-title[Ocean currents]

.italic[Parameters:] the global constants $\theta$ of the ocean model, such as its viscosity $\nu$.
]

.footnote[Illustration: 2D turbulence on a $\beta$-plane, same forcing, three viscosities; current speed.]

???

The currents follow the Navier–Stokes equations on a rotating Earth. Their constants, such as the viscosity, the mixing or the bottom drag, are poorly known. These are $\theta$. Here, three values of the viscosity give three different oceans.

The same structure appears whenever an instrument stands between us and the system we study.

---

class: black-slide

.bg-video[<video autoplay muted loop playsinline poster="figures/gw-x-poster.jpg?v=2" src="figures/videos/gw-x.mp4?v=2"></video>]

.overlay-box.overlay-top-left[
.overlay-title[Gravitational waves]

.italic[Observations:] the strain $x$ recorded by LIGO. In time and frequency, a chirp rises out of the noise.
]

.footnote[Data: LIGO Hanford, GW150914, September 14, 2015 ([GWOSC](https://gwosc.org/events/GW150914/)). Whitened strain, band-passed 35–350 Hz (white), and its wavelet transform, 20–512 Hz.]

???

Second example, gravitational waves. This is the signal recorded by LIGO on September 14, 2015. Time goes to the right, frequency up. Most of the strain, in white, is noise. In a fraction of a second, a chirp appears, a signal whose frequency rises quickly. This is $x$.

---

class: black-slide

.bg-video[<video autoplay muted loop playsinline poster="figures/gw-z-poster.jpg" src="figures/videos/gw-z.mp4"></video>]

.overlay-box.overlay-top-left[
.overlay-title[Gravitational waves]

.italic[Latent states:] the signal $z$ of two black holes that spiral into each other, merge, and ripple space-time.
]

.footnote[Simulation: B. J. Kelly, C. Henze, T. Sandstrom, [NASA SVS 13197](https://svs.gsfc.nasa.gov/13197).]

???

The chirp comes from two black holes that spiral into each other and merge. General relativity predicts the waveform. This is $z$.

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

The waveform depends on fifteen parameters of the binary, including the two masses, the two spins, the distance, the orientation and the sky position. This is $\theta$.

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

Third example, exoplanets. These are the four planets of HR 8799, imaged directly over seven years, with the star masked. The light of a planet, dispersed by a spectrograph, gives a spectrum from 1 to 2.5 microns. This is $x$.

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

The spectrum comes from the atmosphere, its temperature profile, its molecules and its clouds. Here, the silicate clouds seen by JWST on VHS 1256 b. This is $z$.

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

The atmosphere follows from a few bulk parameters, such as the C/O ratio, the metallicity, the gravity, the radius, the clouds and the mixing. These ten hot Jupiters range from clear to cloudy. The parameters also tell where and how the planet formed. This is $\theta$.

---

class: middle

.center.width-80[![](figures/setup.svg)]

## Inverse problems in science

Given an observation $x$, estimate the posterior distribution
$$p(\theta | x) = \frac{p(x|\theta) p(\theta)}{p(x)}, \quad \text{with} \quad p(x | \theta) = \int p(x | z) p(z | \theta) \text{d}z,$$
of the parameters $\theta$, with the latent states $z$ integrated out.

???

The three examples share one structure. Parameters $\theta$ set the physics, the physics produces a state $z$, and an instrument turns $z$ into an observation $x$.

We want the posterior over $\theta$. The likelihood requires integrating over every state $z$ that could have produced $x$, which is intractable. We can simulate the chain, but we cannot evaluate it.

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

Generation runs from left to right, through the prior, the physics and the instrument. Each step is a simulator we trust. Inference runs from right to left, from $x$ back to $\theta$.

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

We use a small simulator throughout the tutorial. It is a toy, with the same structure as a real retrieval code.

It has six parameters, the internal temperature, the gravity, the metallicity, the C/O ratio, the cloud-top pressure and the radius. The prior is uniform over each range.

---

class: middle

## A minimal exoplanet simulator

Physics, $z \sim p(z | \theta)$: a temperature profile, chemistry, and a cloud deck.

.center[
<video poster="figures/toy-walk-2.png" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-walk-2.mp4" type="video/mp4">
</video>
]

???

The physics gives the atmosphere, that is, a temperature profile, the abundances of water, methane and carbon monoxide, and a cloud deck. This is $z$. Methane appears where the atmosphere is cool enough.

As in petitRADTRANS retrievals, the profile is parameterized, not self-consistent. It is a grey Eddington profile set by the internal temperature and the gravity.

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

Radiative transfer gives the emitted light. The dips are water and methane bands. The peaks are windows into deeper, hotter layers.

---

class: middle

## A minimal exoplanet simulator

Instrument, $x \sim p(x | z)$: binned, with noise.

.center[
<video poster="figures/toy-walk-4.png" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-walk-4.mp4" type="video/mp4">
</video>
]

???

The instrument bins the light and adds noise. This is $x$. Everything to its left is hidden.

The simulator is easy to run forward. The question is how to go back.

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

Before any data, we check the prior and the simulator together. We simulate from the prior and reduce each spectrum to a summary statistic known from other objects, here the J − K colour. Known brown dwarfs and directly imaged planets lie roughly between −1 and 3.

Our toy fails this check. 42% of the prior draws are redder than any known object, so the prior or the physics, or both, should be revised.

The check uses domain knowledge only. Tuning the prior to the observation would use the data twice. It also costs nothing, since these simulations are the training set of NPE.

---

class: black-slide

.bg-video[<video autoplay muted loop playsinline poster="figures/galaxy-1.jpg?v=6" src="figures/videos/galaxy-1.mp4?v=6"></video>]

.overlay-box.overlay-bottom-left.narrow-box[
.overlay-title[Inference algorithms]

Estimating $p(\theta | x)$: classical methods in blue, simulation-based inference in pink.
]

???

Many algorithms invert the simulator. In blue, the classical ones, MCMC, nested sampling and ABC. In pink, simulation-based inference with neural networks, which estimates the posterior, the likelihood or the likelihood ratio.

---

count: false
class: black-slide

.bg-video[<video autoplay muted playsinline poster="figures/galaxy-2.jpg?v=6" src="figures/videos/galaxy-2.mp4?v=6"></video>]

.overlay-box.overlay-bottom-left.narrow-box[
.overlay-title[Inference algorithms]

Estimating $p(\theta | x)$: classical methods in blue, simulation-based inference in pink.
]

???

We focus on two of them, neural posterior estimation (NPE) and its flow-matching variant (FMPE). NPE is the simplest, and the most used so far for exoplanets.

---

class: middle

## Neural posterior estimation

We train a conditional density estimator $q\_\phi(\theta | x)$, typically a .bold[normalizing flow], to approximate the posterior of .bold[any] observation $x$,
$$\phi^\star = \arg\min\_\phi \; \mathbb{E}\_{p(\theta)} \mathbb{E}\_{p(x | \theta)} \left[ -\log q\_\phi(\theta | x) \right].$$

The parameters are drawn from the prior and the observations from the simulator, so that the likelihood is sampled, never evaluated.

Up to a constant, this loss is the expected divergence to the true posterior,
$$\mathbb{E}\_{p(x)} \, \text{KL}\big( p(\theta|x) \, \Vert \, q\_\phi(\theta|x) \big).$$

???

NPE trains a network that maps an observation $x$ to a distribution over $\theta$. The network is typically a normalizing flow.

The training pairs come from the simulator. The loss is the negative log-probability of the true $\theta$ given $x$. Up to a constant, it is the expected KL divergence to the true posterior, so its minimum is the posterior itself. The likelihood is never evaluated.

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

The network has two parts. An embedding network compresses the spectrum into a few learned features. A normalizing flow, three spline transforms conditioned on these features, maps $\theta$ to a standard Gaussian.

The map is invertible with a tractable Jacobian, so the density follows from the change of variables. To sample, we draw from the Gaussian and invert the map.

Below the flow, samples for our observed spectrum become, layer by layer, a round Gaussian.

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

The animation passes six spectra through the trained network. The colours show the actual values of a few units, relative to their average over these spectra, and the 64 features change with each spectrum.

The embedding network is a choice, like the prior or the flow. Here, the spectrum has 94 bins on a fixed grid, so a multilayer perceptron suffices. Each layer multiplies its input by a matrix, adds a vector, and applies a simple nonlinear function, here the ELU. Four such layers take the 94 bins to 512, 256, 256 and finally 64 features, which condition the flow. We did not compare it with other architectures on this toy; the posterior already matches MCMC.

The weights are not set by hand. The same loss trains the embedding and the flow together, so the features are those that best inform the posterior. They replace hand-crafted summary statistics. On our toy, the trained network reads the C/O ratio from the CO and CH4 bands, the cloud top from the windows, and the radius from the continuum peaks. Nobody told it where the molecules absorb.

Other data call for other choices. Convolutional networks share filters along wavelength and scale to thousands of bins. Transformers take each bin or segment with its wavelength and error bar, which suits irregular grids and combined instruments, as for WISE 1738. Residual connections help when the network is deep.

---

class: middle

## Training

We simulate $N$ pairs $(\theta\_i, x\_i) \sim p(\theta, x)$ and minimize the empirical estimate of the loss,
$$L(\phi) = \mathbb{E}\_{p(\theta, x)} \left[ -\log q\_\phi(\theta | x) \right] \approx \frac{1}{N} \sum\_{i=1}^{N} -\log q\_\phi(\theta\_i | x\_i),$$
with the noise added on the fly.

.center[
<video poster="figures/toy-training.png" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-training.mp4" type="video/mp4">
</video>
]

???

We simulate half a million pairs, in half an hour on a laptop. Each line is one planet, coloured by its internal temperature. With petitRADTRANS, twelve million spectra took about 17,000 CPU hours. This cost is paid once.

We minimize the empirical loss by stochastic gradient descent. The noise is redrawn at each epoch. The loss decreases on training and validation pairs.

---

class: middle

## Amortization

Once trained, the network gives the posterior of any new spectrum in a fraction of a second.

.center[
<video poster="figures/toy-gallery.png?v=3" muted loop autoplay playsinline class="anim">
<source src="figures/videos/toy-gallery.mp4?v=3" type="video/mp4">
</video>
]

???

The network is trained once, for this simulator and this prior. Each new spectrum then gets its posterior immediately.

Here, ten new planets. NPE handles all of them in about two seconds, where MCMC or nested sampling would take an hour and a half. Some posteriors are wider than others, because some spectra constrain their planet less. For a survey of hundreds of planets, this changes what is possible.

---

class: middle

## Results on the toy problem

Consider an observed spectrum $x\_{\rm obs}$, simulated from known parameters $\theta^\star$ hidden from the methods.

.center.width-100[![](figures/toy-xobs.png)]

???

We now apply the trained network to an observed spectrum. We simulated it ourselves, so we know the true parameters and can check the answer.

---

class: middle

.center.width-65[![](figures/toy-corner.png)]

???

In red, NPE. In grey, MCMC, and in orange, nested sampling, both with the exact likelihood. The three agree and contain the true parameters, in blue.

NPE took two seconds, MCMC nine minutes and nested sampling about an hour. With a real radiative transfer code, the last two take days.

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

The first check tests the network. Posteriors are cheap, so we compute a thousand of them for simulated spectra whose parameters we know.

On the left, the 90% credible interval of the C/O ratio for each test case. Green intervals contain the true value, red ones miss it. On the right, the same count at every credibility level, the expected coverage. The gray bands show where a perfectly calibrated network would land by chance with this many cases, at one, two and three sigma. They narrow as cases accumulate. The curve stays within them, so the posteriors are calibrated. Above would be conservative, below overconfident.

Coverage is necessary but not sufficient, since the prior is calibrated too. TARP, MIRA and L-C2ST are stronger tests.

The check took a minute. With MCMC, a thousand retrievals would take a week.

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

In a benchmark of common SBI algorithms, many were overconfident on some problems, even with the recommended training. An overconfident posterior claims what the data do not support.

Balanced NPE adds a regularizer to the loss, which makes posteriors calibrated or conservative. The curves move above the diagonal.

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

The second check tests the forward model, which calibration cannot do. We draw parameters from the posterior, simulate, and compare with the observation. The simulated spectra cover the data within the noise.

---

class: middle

## When the model is wrong

.center.width-100[![](figures/toy-misspec-obs.png)]

Consider now a new observation of the same planet, with an absorption band at 1.52 μm that the simulator does not have.

???

So far, the simulator was correct. Here, we add an absorption band at 1.52 microns, where ammonia absorbs in cool atmospheres. Our simulator has no ammonia. In dashed grey, the same planet without the band.

---

class: middle

.center.width-100[![](figures/toy-misspec.png?v=2)]

.center[The posteriors are .bold[confident and exact, but wrong], because of misspecification.]

.footnote[Detecting and handling misspecification: [Schmitt et al](https://arxiv.org/abs/2112.08866), 2023; [Ward et al](https://arxiv.org/abs/2210.06564), NeurIPS 2022.]

???

On the left, the posteriors of the gravity and the radius. NPE, MCMC and nested sampling agree, are tight, and all miss the truth. The gravity even hits the edge of the prior. MCMC and nested sampling are exact, but for the wrong model.

Calibration does not catch this, since it is computed on simulated spectra. The posterior predictive check does. The fit looks fine by eye, but two residuals reach five to six sigma at the missing band.

The fix is in the model, by adding the physics or inflating the noise model.

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

Our 2023 paper with Malavika Vasist, François Rozet and Olivier Absil first applied NPE to atmospheric retrieval. The benchmark spectrum is simulated, modelled on HR 8799 e.

The simulator is petitRADTRANS with sixteen parameters, including clouds and disequilibrium chemistry. Training used twelve million simulations, about 17,000 CPU hours.

On the left, NPE agrees with MultiNest. On the right, the same two checks as on the toy. The posterior predictive reproduces the observation, and the coverage lies on the diagonal.

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

This is real data. WISE 1738 is a brown dwarf at about 400 kelvin, a proxy for cold giant planets. We combined JWST/MIRI with near-infrared spectra from HST and Gemini.

NPE finds water, methane and ammonia, and also carbon monoxide and carbon dioxide, a sign of vertical mixing. It constrains the isotopologue 15-ammonia for the first time. The posteriors passed coverage and other diagnostics.

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

Any conditional density estimator can serve in NPE. On the left, a discrete flow, as we used. It composes a few invertible transformations, whose architecture must keep the Jacobian tractable. On the right, a continuous flow, where an unconstrained network defines a vector field and an ODE moves samples from the Gaussian to the posterior. It is more flexible. Both networks also take the noise level as input. Continuous flows tend to scale better with the number of parameters; for gravitational waves, with 15 parameters, flow matching outperformed discrete flows.

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

Samples move along a vector field, from noise at time zero to the posterior at time one. Sampling means solving an ODE.

---

class: middle

As for discrete flows, the density is exact,
$$\begin{aligned} \log q\_\phi(\theta | x) &= \log \mathcal{N}(\theta\_0; 0, I) + \int\_1^0 \text{tr} \left( \frac{\partial v\_\phi(\theta\_t, t; x)}{\partial \theta\_t} \right) dt \\\\ &= \log \mathcal{N}(\theta\_0; 0, I) + \int\_1^0 \nabla \cdot v\_\phi(\theta\_t, t; x) \, dt, \end{aligned}$$
where $\theta\_0$ is the noise that $\theta$ flows back to at $t = 0$. The vector field is trained by regression along straight paths $\theta\_t = (1-t)\, \theta\_0 + t\, \theta$,
$$\min\_\phi \; \mathbb{E}\_{t \sim \mathcal{U}(0,1),\; \theta\_0 \sim \mathcal{N}(0, I),\; (\theta, x) \sim p(\theta, x)} \left[ \left\Vert v\_\phi(\theta\_t, t; x) - (\theta - \theta\_0) \right\Vert^2 \right],$$
which requires no integration of the flow.

.footnote[[Dax et al](https://arxiv.org/abs/2305.17161), NeurIPS 2023.]

???

The density is exact, as for discrete flows. We follow the flow backwards, from the parameters to the noise. The sum of log-determinants becomes an integral of the trace of the Jacobian, which is also the divergence of the vector field.

The vector field is trained by flow matching. We draw noise and a simulated pair, and take a point on the straight line from the noise to the parameters. The network should point along that line. Training is a regression, with no constraint on the architecture.

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

This is the paper by Timothy Gebhard, Jonas Wildberger, Max and colleagues, on the same benchmark.

The network takes the noise level as input, so one network covers any signal-to-noise ratio. Samples are reweighted by importance sampling, which corrects the network and gives the evidence.

On the left, FMPE and NPE, with and without importance sampling, agree with two nested samplers. On the right, FMPE is usually the better proposal.

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

When the likelihood can be evaluated, even at a cost, the network becomes a proposal. Each sample gets a weight, the likelihood times the prior over the density of the network. This requires an exact density.

The animation shows the three steps, sampling, weighting and resampling. The result lands on MCMC.

The efficiency, here about 60%, measures the quality of the proposal. The mean weight is the evidence. The cost is a few thousand likelihood evaluations, not millions.

---

class: middle

.center.width-70[![](figures/toy-is-corner.png)]

.center[With importance sampling (blue), NPE matches MCMC (grey).]

???

All six parameters. In red, the network alone. In blue, after importance sampling. In grey, MCMC. Blue and grey coincide.

---

class: middle

## Model comparison

We compare two simulators, with and without a cloud deck. By eye, both fit.

.center.width-100[![](figures/mc-ppc.png)]

???

Clouds or a molecule detection are questions about models. We compare the toy with clouds, six parameters, and without, five parameters.

On the left, a cloudy planet. Both models fit by eye, but the clear model misses a few bins by two or three sigma. Its chi-square is worse by about 47, and the log Bayes factor is 20.

On the right, a clear planet. Both models fit, the cloudy one by putting its clouds deep. The log Bayes factor of about minus one is the Occam penalty for the unneeded cloud parameter.

---

class: middle

<img src="figures/mc-bayes.png" style="display: block; margin: 0 auto; width: 46%;">

The .bold[Bayes factor] $B = p(x | \text{cloudy}) \,/\, p(x | \text{clear})$ compares the evidence of the two models.

<div class="evidence-rows">
<div><span>Nested sampling</span>$$p(x|M) \approx \sum_i p(x|\theta_i, M) \, \Delta X_i$$</div>
<div><span>Importance sampling</span>$$p(x|M) \approx \frac{1}{n} \sum_i \frac{p(x|\theta_i, M) \, p(\theta_i|M)}{q_\phi(\theta_i|x)} = \frac{1}{n} \sum_i w_i$$</div>
<div><span>Classifier</span>$$\log B \approx \log \frac{d_\psi(x)}{1 - d_\psi(x)}, \quad d_\psi(x) \approx p(\text{cloudy}|x)$$</div>
</div>

.footnote[Classifier: [Radev et al](https://arxiv.org/abs/2004.10629), 2020. Model comparison without the evidence: MIRA, [Sharief et al](https://arxiv.org/abs/2605.02014), ICML 2026.]


???

The Bayes factor is the ratio of the evidences, the probabilities of the observation under each model. We estimate it in three ways.

Nested sampling is the reference, with fifty thousand to a million likelihood calls per spectrum and model. Importance sampling gives the same answer, as the mean weight. A classifier needs no likelihood. Its log-odds give the Bayes factor, but they saturate on the cloudy planet, which is enough for a decision, not for a value.

---

class: black-slide, middle

.bg-video[<video autoplay muted loop playsinline poster="figures/exo-x-poster.jpg" src="figures/videos/exo-x.mp4" style="filter: brightness(0.55);"></video>]

.punch[
.punch-title[Summary]

Inference requires a simulator, not a likelihood.

A neural posterior estimator is trained once; it then gives the posterior of any spectrum in seconds.

Calibration tests the network; posterior predictive checks test the model.

An overdispersed posterior is safer than an overconfident one.

With a likelihood, importance sampling corrects the network and gives the evidence, for model comparison.
]

???

Five points to remember.

Inference requires a simulator, not a likelihood. Make the simulator as realistic as needed, not as convenient as the sampler requires.

NPE is trained once and then gives posteriors in seconds, which makes diagnostics affordable.

Calibration tests the network, posterior predictive checks test the model, and the evidence compares models. With a likelihood, importance sampling makes the posterior exact.

Prefer an overdispersed posterior to an overconfident one. The network has seen only what the simulator produces, and outside of it, it still answers.

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

Our review with Max is the most direct follow-up to this tutorial. The PNAS paper is a short overview, the practical guide covers the workflow, and the tutorial review covers diffusion and flow-matching estimators. The second list gives the exoplanet papers in chronological order.

---

class: black-slide
background-image: url(figures/title-bg.jpg)
background-size: cover

.closing-end[The end.]

???

A prior, physics and an instrument make a simulator. We cannot evaluate the likelihood, but we can simulate, and that is enough.

Thank you.
