import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  AppShell,
  Badge,
  Button,
  Card,
  Divider,
  Grid,
  Group,
  Image,
  List,
  Loader,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Title,
} from '@mantine/core'
import { Dropzone, type FileWithPath } from '@mantine/dropzone'
import { notifications } from '@mantine/notifications'
import {
  IconAtom2,
  IconArrowRight,
  IconBrandGithub,
  IconBrain,
  IconChartDots3,
  IconDatabaseSearch,
  IconInfoCircle,
  IconScan,
  IconSchool,
  IconUpload,
  IconUsersGroup,
} from '@tabler/icons-react'
import Plotly from 'plotly.js-dist-min'
import createPlotlyComponent from 'react-plotly.js/factory'
import './App.css'
import heroImage from './assets/hero.png'
import {
  calculateChemistryMetrics,
  createDemoSession,
  fetchSpectrum,
  fetchXic,
  uploadDataset,
} from './api'
import type { ChemistryMetrics, SessionResponse, SpectrumResponse, XicResponse } from './types'

const Plot = createPlotlyComponent(Plotly as never)

const chargeOptions = ['1', '2', '3', '4', '5'].map((value) => ({
  value,
  label: `+${value}`,
}))

function formatCompact(value: number | undefined): string {
  if (value === undefined) {
    return 'n/a'
  }
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 2,
  }).format(value)
}

function formatFixed(value: number | undefined, fractionDigits = 2): string {
  if (value === undefined || Number.isNaN(value)) {
    return 'n/a'
  }
  return value.toFixed(fractionDigits)
}

function parseNumber(value: string): number | null {
  const parsed = Number(value)
  if (Number.isFinite(parsed)) {
    return parsed
  }
  return null
}

function pickDefaultRt(session: SessionResponse): number | null {
  if (!session.tic?.length) {
    return null
  }
  return session.tic.reduce((best, current) =>
    current.intensity > best.intensity ? current : best
  ).rt
}

function App() {
  const currentPath =
    typeof window === 'undefined' ? '/' : window.location.pathname.replace(/\/+$/, '') || '/'
  const isWorkspace = currentPath === '/lcms'
  const [session, setSession] = useState<SessionResponse | null>(null)
  const [selectedRt, setSelectedRt] = useState<number | null>(null)
  const [spectrum, setSpectrum] = useState<SpectrumResponse | null>(null)
  const [xic, setXic] = useState<XicResponse | null>(null)
  const [chemistry, setChemistry] = useState<ChemistryMetrics | null>(null)
  const [uploading, setUploading] = useState(false)
  const [loadingSpectrum, setLoadingSpectrum] = useState(false)
  const [loadingXic, setLoadingXic] = useState(false)
  const [loadingChemistry, setLoadingChemistry] = useState(false)
  const [targetMz, setTargetMz] = useState('')
  const [ppmTolerance, setPpmTolerance] = useState('10')
  const [neutralMass, setNeutralMass] = useState('500')
  const [charge, setCharge] = useState('2')
  const [observedMz, setObservedMz] = useState('')

  const readySession = session?.status === 'ready' ? session : null

  useEffect(() => {
    if (!readySession || selectedRt === null) {
      return
    }

    let cancelled = false
    setLoadingSpectrum(true)
    fetchSpectrum(readySession.sessionId, selectedRt)
      .then((payload) => {
        if (cancelled) {
          return
        }
        setSpectrum(payload)
        if (!targetMz && payload.peakLabels.length > 0) {
          const topPeak = [...payload.peakLabels].sort((a, b) => b.intensity - a.intensity)[0]
          setTargetMz(topPeak.mz.toFixed(4))
        }
      })
      .catch((error: Error) => {
        if (!cancelled) {
          notifications.show({
            color: 'red',
            title: 'Spectrum lookup failed',
            message: error.message,
          })
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingSpectrum(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [readySession, selectedRt, targetMz])

  const summaryCards = useMemo(() => {
    if (!readySession?.summary) {
      return []
    }

    const summary = readySession.summary
    return [
      { label: 'Scans', value: summary.scanCount.toString() },
      { label: 'RT window', value: `${formatFixed(summary.rtMin)} - ${formatFixed(summary.rtMax)} min` },
      { label: 'm/z window', value: `${formatFixed(summary.mzMin, 1)} - ${formatFixed(summary.mzMax, 1)}` },
      { label: 'Max intensity', value: formatCompact(summary.intensityMax) },
    ]
  }, [readySession])

  const selectedRtLabel =
    selectedRt === null ? 'No retention time selected' : `${formatFixed(selectedRt, 2)} min`

  if (!isWorkspace) {
    return (
      <AppShell padding="md" header={{ height: 76 }}>
        <AppShell.Header className="app-header">
          <Group justify="space-between" align="center" h="100%" px="lg">
            <div>
              <Title order={2}>OpenChemLab</Title>
              <Text c="dimmed" size="sm">
                Browser-based chemistry tools for students, labs, and teaching teams.
              </Text>
            </div>
            <Button component="a" href="/lcms" rightSection={<IconArrowRight size={16} />}>
              Open LC-MS tool
            </Button>
          </Group>
        </AppShell.Header>

        <AppShell.Main className="landing-page">
          <Stack gap="xl">
            <Paper className="landing-hero" radius="xl" p="xl">
              <Grid gutter="xl" align="center">
                <Grid.Col span={{ base: 12, lg: 7 }}>
                  <Stack gap="md">
                    <Badge color="teal" variant="light" w="fit-content">
                      OpenChemLab for accessible chemistry software
                    </Badge>
                    <Title order={1} className="landing-title">
                      Chemistry tools that work in the browser, even when vendor software does not.
                    </Title>
                    <Text size="lg" c="dimmed">
                      OpenChemLab is for students learning analytical chemistry, teachers preparing
                      practical demonstrations, and small research teams who want shareable,
                      browser-first workflows.
                    </Text>
                    <Group>
                      <Button
                        component="a"
                        href="/lcms"
                        size="md"
                        rightSection={<IconArrowRight size={16} />}
                      >
                        Go to LC-MS spectrogram
                      </Button>
                      <Button component="a" href="#who-its-for" variant="light" size="md">
                        Who is this for?
                      </Button>
                      <Button component="a" href="#about" variant="subtle" size="md">
                        About the creator
                      </Button>
                    </Group>
                  </Stack>
                </Grid.Col>
                <Grid.Col span={{ base: 12, lg: 5 }}>
                  <Paper className="landing-visual" radius="xl" p="md">
                    <Image
                      src={heroImage}
                      alt="OpenChemLab preview illustration"
                      radius="lg"
                      className="landing-image"
                    />
                  </Paper>
                </Grid.Col>
              </Grid>
            </Paper>

            <SimpleGrid id="who-its-for" cols={{ base: 1, md: 3 }} spacing="lg">
              <Card className="landing-card" withBorder radius="xl" padding="lg">
                <ThemeIcon color="teal" variant="light" size={44} radius="xl">
                  <IconSchool size={22} />
                </ThemeIcon>
                <Title order={3} mt="md">
                  Students
                </Title>
                <Text c="dimmed" mt="xs">
                  Use modern chemistry tools without depending on Windows-only vendor software or
                  lab-specific installations.
                </Text>
              </Card>

              <Card className="landing-card" withBorder radius="xl" padding="lg">
                <ThemeIcon color="grape" variant="light" size={44} radius="xl">
                  <IconUsersGroup size={22} />
                </ThemeIcon>
                <Title order={3} mt="md">
                  Teaching labs
                </Title>
                <Text c="dimmed" mt="xs">
                  Share one browser-first workflow with a whole class instead of troubleshooting
                  local desktop setup on every machine.
                </Text>
              </Card>

              <Card className="landing-card" withBorder radius="xl" padding="lg">
                <ThemeIcon color="cyan" variant="light" size={44} radius="xl">
                  <IconChartDots3 size={22} />
                </ThemeIcon>
                <Title order={3} mt="md">
                  Small research teams
                </Title>
                <Text c="dimmed" mt="xs">
                  Put targeted tools online quickly so collaborators can inspect data from anywhere
                  with a browser.
                </Text>
              </Card>
            </SimpleGrid>

            <Paper className="landing-callout" radius="xl" p="xl">
              <Grid gutter="xl" align="center">
                <Grid.Col span={{ base: 12, md: 8 }}>
                  <Stack gap="sm">
                    <Badge color="violet" variant="light" w="fit-content">
                      Current tool
                    </Badge>
                    <Title order={2}>LC-MS Spectrogram</Title>
                    <Text c="dimmed">
                      Explore LC-MS maps, total ion chromatograms, extracted ion traces, and
                      scan-level spectra from the browser. Thermo RAW is optional when a parser is
                      installed; mzML works out of the box.
                    </Text>
                  </Stack>
                </Grid.Col>
                <Grid.Col span={{ base: 12, md: 4 }}>
                  <Button
                    component="a"
                    href="/lcms"
                    fullWidth
                    size="md"
                    rightSection={<IconArrowRight size={16} />}
                  >
                    Enter the LC-MS workspace
                  </Button>
                </Grid.Col>
              </Grid>
            </Paper>

            <Paper id="about" className="about-panel" radius="xl" p="xl">
              <Grid gutter="xl" align="center">
                <Grid.Col span={{ base: 12, lg: 7 }}>
                  <Stack gap="md">
                    <Badge color="dark" variant="light" w="fit-content">
                      About the creator
                    </Badge>
                    <Title order={2}>Built for people who deserve useful software, not unnecessary barriers.</Title>
                    <Text c="dimmed" size="lg">
                      OpenChemLab is shaped by a simple idea: meaningful software should help other
                      people learn, explore, and do better work. The project sits at the
                      intersection of scientific tooling and accessible web software.
                    </Text>
                    <Text c="dimmed">
                      The broader interests behind it include AI and machine learning research,
                      bioinformatics, and neuroscience, with a strong focus on tools that are
                      practical enough to matter in real educational and research settings.
                    </Text>
                    <Group>
                      <Button
                        component="a"
                        href="https://github.com/lowoncuties"
                        target="_blank"
                        rel="noreferrer"
                        leftSection={<IconBrandGithub size={16} />}
                      >
                        GitHub: @lowoncuties
                      </Button>
                    </Group>
                  </Stack>
                </Grid.Col>
                <Grid.Col span={{ base: 12, lg: 5 }}>
                  <Card className="about-card" withBorder radius="xl" padding="lg">
                    <Stack gap="md">
                      <ThemeIcon color="dark" variant="light" size={46} radius="xl">
                        <IconBrain size={22} />
                      </ThemeIcon>
                      <Title order={3}>Research interests</Title>
                      <SimpleGrid cols={2} spacing="sm">
                        <Badge variant="light" color="teal" size="lg">
                          AI / ML
                        </Badge>
                        <Badge variant="light" color="cyan" size="lg">
                          Bioinformatics
                        </Badge>
                        <Badge variant="light" color="grape" size="lg">
                          Neuroscience
                        </Badge>
                        <Badge variant="light" color="lime" size="lg">
                          Scientific software
                        </Badge>
                      </SimpleGrid>
                      <Text size="sm" c="dimmed">
                        OpenChemLab is meant to grow into a collection of focused tools that make
                        chemistry workflows easier to access, share, and teach.
                      </Text>
                    </Stack>
                  </Card>
                </Grid.Col>
              </Grid>
            </Paper>
          </Stack>
        </AppShell.Main>
      </AppShell>
    )
  }

  async function handleUpload(files: FileWithPath[]) {
    const file = files[0]
    if (!file) {
      return
    }

    setUploading(true)
    setXic(null)
    setSpectrum(null)
    setChemistry(null)
    try {
      const payload = await uploadDataset(file)
      setSession(payload)
      const defaultRt = payload.status === 'ready' ? pickDefaultRt(payload) : null
      setSelectedRt(defaultRt)
      notifications.show({
        color: payload.status === 'ready' ? 'teal' : 'yellow',
        title: payload.status === 'ready' ? 'Dataset ready' : 'Upload received',
        message: payload.message,
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Upload failed.'
      notifications.show({
        color: 'red',
        title: 'Upload failed',
        message,
      })
    } finally {
      setUploading(false)
    }
  }

  async function handleLoadDemo() {
    setUploading(true)
    setXic(null)
    setSpectrum(null)
    setChemistry(null)
    try {
      const payload = await createDemoSession()
      setSession(payload)
      setSelectedRt(pickDefaultRt(payload))
      notifications.show({
        color: 'teal',
        title: 'Demo dataset loaded',
        message: payload.message,
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to load demo data.'
      notifications.show({
        color: 'red',
        title: 'Demo load failed',
        message,
      })
    } finally {
      setUploading(false)
    }
  }

  async function handleRunXic() {
    if (!readySession) {
      return
    }
    const mz = parseNumber(targetMz)
    const ppm = parseNumber(ppmTolerance)
    if (mz === null || ppm === null) {
      notifications.show({
        color: 'red',
        title: 'Invalid XIC settings',
        message: 'Enter numeric values for target m/z and ppm tolerance.',
      })
      return
    }

    setLoadingXic(true)
    try {
      const payload = await fetchXic(readySession.sessionId, mz, ppm)
      setXic(payload)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to calculate XIC.'
      notifications.show({
        color: 'red',
        title: 'XIC failed',
        message,
      })
    } finally {
      setLoadingXic(false)
    }
  }

  async function handleChemistry() {
    const parsedMass = parseNumber(neutralMass)
    const parsedObserved = observedMz ? parseNumber(observedMz) : null
    if (parsedMass === null) {
      notifications.show({
        color: 'red',
        title: 'Invalid chemistry input',
        message: 'Neutral mass must be a number.',
      })
      return
    }

    setLoadingChemistry(true)
    try {
      const payload = await calculateChemistryMetrics({
        neutralMass: parsedMass,
        charge: Number(charge),
        observedMz: parsedObserved === null ? undefined : parsedObserved,
      })
      setChemistry(payload)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to compute chemistry metrics.'
      notifications.show({
        color: 'red',
        title: 'Calculation failed',
        message,
      })
    } finally {
      setLoadingChemistry(false)
    }
  }

  return (
    <AppShell padding="md" header={{ height: 76 }}>
      <AppShell.Header className="app-header">
        <Group justify="space-between" align="center" h="100%" px="lg">
          <div>
            <Title order={2}>LC–MS spectrogram</Title>
            <Text c="dimmed" size="sm">
              Thermo RAW and mzML: maps, chromatograms, and spectra in the browser.
            </Text>
          </div>
          <Button component="a" href="/" variant="subtle">
            OpenChemLab home
          </Button>
        </Group>
      </AppShell.Header>

      <AppShell.Main>
        <Stack gap="lg">
          <Paper className="hero-card" radius="xl" p="xl">
            <Grid gutter="xl" align="center">
              <Grid.Col span={{ base: 12, md: 7 }}>
                <Stack gap="sm">
                  <Title order={1}>Retention time, m/z, and ion traces</Title>
                  <Text c="dimmed" size="md">
                    Upload Thermo RAW (converted server-side when a parser is configured) or mzML.
                    Use the demo dataset if no file is available.
                  </Text>
                  <List
                    spacing="sm"
                    icon={
                      <ThemeIcon color="violet" variant="light" size={24} radius="xl">
                        <IconAtom2 size={16} />
                      </ThemeIcon>
                    }
                  >
                    <List.Item>2D LC–MS map: retention time and m/z.</List.Item>
                    <List.Item>TIC, XIC, and centroid spectrum with peak labels.</List.Item>
                    <List.Item>Theoretical m/z, isotope spacing, and ppm error from mass and charge.</List.Item>
                  </List>
                </Stack>
              </Grid.Col>
              <Grid.Col span={{ base: 12, md: 5 }}>
                <Card withBorder radius="lg" padding="lg">
                  <Stack gap="md">
                    <Title order={3}>Load data</Title>
                    <Dropzone
                      onDrop={handleUpload}
                      maxFiles={1}
                      loading={uploading}
                      accept={{
                        'application/octet-stream': ['.raw'],
                        'application/xml': ['.mzML'],
                        'text/xml': ['.mzML'],
                      }}
                    >
                      <Group justify="center" gap="md" mih={180}>
                        <ThemeIcon size={52} radius="xl" variant="light" color="violet">
                          {uploading ? <Loader size="sm" /> : <IconUpload size={26} />}
                        </ThemeIcon>
                        <div>
                          <Text fw={600}>Drop `.raw` or `.mzML` here</Text>
                          <Text size="sm" c="dimmed">
                            RAW files are converted on the backend when ThermoRawFileParser or
                            `msconvert` is available.
                          </Text>
                        </div>
                      </Group>
                    </Dropzone>
                    <Button variant="light" onClick={handleLoadDemo} loading={uploading}>
                      Load demo data
                    </Button>
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          </Paper>

          {session && (
            <Alert
              variant="light"
              color={session.status === 'ready' ? 'teal' : session.status === 'conversion_error' ? 'yellow' : 'red'}
              icon={<IconInfoCircle size={18} />}
              title={session.filename}
            >
              <Text>{session.message}</Text>
              {session.notes.length > 0 && (
                <List size="sm" mt="sm">
                  {session.notes.map((note) => (
                    <List.Item key={note}>{note}</List.Item>
                  ))}
                </List>
              )}
            </Alert>
          )}

          <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }}>
            {summaryCards.map((item) => (
              <Card key={item.label} withBorder radius="lg" padding="lg">
                <Text size="sm" c="dimmed">
                  {item.label}
                </Text>
                <Text size="xl" fw={700}>
                  {item.value}
                </Text>
              </Card>
            ))}
          </SimpleGrid>

          <Grid gutter="lg">
            <Grid.Col span={{ base: 12, lg: 8 }}>
              <Card withBorder radius="lg" padding="lg">
                <Group justify="space-between" mb="sm">
                  <div>
                    <Title order={3}>LC-MS map</Title>
                    <Text size="sm" c="dimmed">
                      Click a point to inspect the nearest spectrum around that retention time.
                    </Text>
                  </div>
                  <Badge leftSection={<IconDatabaseSearch size={14} />} variant="dot" color="violet">
                    {selectedRtLabel}
                  </Badge>
                </Group>
                {readySession?.heatmapPoints ? (
                  <Plot
                    data={[
                      {
                        x: readySession.heatmapPoints.map((point) => point.rt),
                        y: readySession.heatmapPoints.map((point) => point.mz),
                        text: readySession.heatmapPoints.map(
                          (point) =>
                            `RT ${formatFixed(point.rt)} min<br/>m/z ${formatFixed(point.mz, 4)}<br/>Intensity ${formatCompact(point.intensity)}`
                        ),
                        type: 'scattergl',
                        mode: 'markers',
                        marker: {
                          size: 8,
                          color: readySession.heatmapPoints.map((point) => Math.log10(point.intensity + 1)),
                          colorscale: 'Viridis',
                          opacity: 0.78,
                        },
                        hovertemplate: '%{text}<extra></extra>',
                      },
                    ]}
                    layout={{
                      autosize: true,
                      height: 420,
                      margin: { l: 56, r: 20, t: 18, b: 56 },
                      paper_bgcolor: 'transparent',
                      plot_bgcolor: 'transparent',
                      xaxis: { title: { text: 'Retention time (min)' }, zeroline: false },
                      yaxis: { title: { text: 'm/z' }, zeroline: false },
                    }}
                    config={{ displaylogo: false, responsive: true }}
                    style={{ width: '100%' }}
                    onClick={(event) => {
                      const point = event.points?.[0]
                      if (point?.x) {
                        setSelectedRt(Number(point.x))
                      }
                    }}
                  />
                ) : (
                  <div className="empty-state">
                    <IconScan size={34} />
                    <Text>Upload a file or load demo data to show the map.</Text>
                  </div>
                )}
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, lg: 4 }}>
              <Stack gap="lg">
                <Card withBorder radius="lg" padding="lg">
                  <Title order={3}>Mass and charge</Title>
                  <Text size="sm" c="dimmed" mb="md">
                    Theoretical m/z, isotope spacing, and ppm error.
                  </Text>
                  <Stack gap="sm">
                    <TextInput
                      label="Neutral mass"
                      value={neutralMass}
                      onChange={(event) => setNeutralMass(event.currentTarget.value)}
                      placeholder="500"
                    />
                    <Select
                      label="Charge state"
                      data={chargeOptions}
                      value={charge}
                      onChange={(value) => setCharge(value ?? '2')}
                    />
                    <TextInput
                      label="Observed m/z"
                      value={observedMz}
                      onChange={(event) => setObservedMz(event.currentTarget.value)}
                      placeholder="optional"
                    />
                    <Button onClick={handleChemistry} loading={loadingChemistry}>
                      Calculate
                    </Button>
                  </Stack>
                  {chemistry && (
                    <>
                      <Divider my="md" />
                      <SimpleGrid cols={1}>
                        <Paper withBorder radius="md" p="sm">
                          <Text size="xs" c="dimmed">
                            Theoretical m/z
                          </Text>
                          <Text fw={700}>{formatFixed(chemistry.theoreticalMz, 4)}</Text>
                        </Paper>
                        <Paper withBorder radius="md" p="sm">
                          <Text size="xs" c="dimmed">
                            Isotope spacing hint
                          </Text>
                          <Text fw={700}>{formatFixed(chemistry.isotopeSpacing, 4)} Th</Text>
                        </Paper>
                        <Paper withBorder radius="md" p="sm">
                          <Text size="xs" c="dimmed">
                            PPM error
                          </Text>
                          <Text fw={700}>
                            {chemistry.ppmError === null ? 'Provide observed m/z' : formatFixed(chemistry.ppmError, 2)}
                          </Text>
                        </Paper>
                      </SimpleGrid>
                    </>
                  )}
                </Card>

                <Card withBorder radius="lg" padding="lg">
                  <Title order={3}>Views</Title>
                  <List
                    mt="sm"
                    spacing="sm"
                    icon={
                      <ThemeIcon color="teal" variant="light" size={24} radius="xl">
                        <IconAtom2 size={16} />
                      </ThemeIcon>
                    }
                  >
                    <List.Item>TIC: total ion signal vs. retention time.</List.Item>
                    <List.Item>XIC: signal within a ppm window around a target m/z.</List.Item>
                    <List.Item>Spectrum: m/z vs. intensity at the selected retention time.</List.Item>
                  </List>
                </Card>
              </Stack>
            </Grid.Col>
          </Grid>

          <Grid gutter="lg">
            <Grid.Col span={{ base: 12, lg: 6 }}>
              <Card withBorder radius="lg" padding="lg">
                <Group justify="space-between" mb="sm">
                  <div>
                    <Title order={3}>Total ion chromatogram</Title>
                    <Text size="sm" c="dimmed">
                      Click the TIC to update the active spectrum.
                    </Text>
                  </div>
                  <Badge variant="light" color="teal">
                    Selected: {selectedRtLabel}
                  </Badge>
                </Group>
                {readySession?.tic ? (
                  <Plot
                    data={[
                      {
                        x: readySession.tic.map((point) => point.rt),
                        y: readySession.tic.map((point) => point.intensity),
                        type: 'scattergl',
                        mode: 'lines',
                        line: { color: '#6c5ce7', width: 2.5 },
                        hovertemplate: 'RT %{x:.2f} min<br/>Intensity %{y:.3s}<extra></extra>',
                      },
                    ]}
                    layout={{
                      autosize: true,
                      height: 320,
                      margin: { l: 56, r: 20, t: 12, b: 52 },
                      paper_bgcolor: 'transparent',
                      plot_bgcolor: 'transparent',
                      xaxis: { title: { text: 'Retention time (min)' } },
                      yaxis: { title: { text: 'Intensity' } },
                      shapes:
                        selectedRt === null
                          ? []
                          : [
                              {
                                type: 'line',
                                x0: selectedRt,
                                x1: selectedRt,
                                y0: 0,
                                y1: 1,
                                yref: 'paper',
                                line: { color: '#16a34a', width: 2, dash: 'dot' },
                              },
                            ],
                    }}
                    config={{ displaylogo: false, responsive: true }}
                    style={{ width: '100%' }}
                    onClick={(event) => {
                      const point = event.points?.[0]
                      if (point?.x) {
                        setSelectedRt(Number(point.x))
                      }
                    }}
                  />
                ) : (
                  <div className="empty-state">
                    <IconChartDots3 size={34} />
                    <Text>The TIC will appear here when a dataset is ready.</Text>
                  </div>
                )}
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, lg: 6 }}>
              <Card withBorder radius="lg" padding="lg">
                <Group justify="space-between" align="end" mb="sm">
                  <div>
                    <Title order={3}>Extracted ion chromatogram</Title>
                    <Text size="sm" c="dimmed">
                      Calculate an XIC for a target m/z and tolerance.
                    </Text>
                  </div>
                  <Group gap="xs">
                    <TextInput
                      className="mz-input"
                      label="Target m/z"
                      value={targetMz}
                      onChange={(event) => setTargetMz(event.currentTarget.value)}
                      placeholder="377.219"
                    />
                    <TextInput
                      className="ppm-input"
                      label="ppm"
                      value={ppmTolerance}
                      onChange={(event) => setPpmTolerance(event.currentTarget.value)}
                      placeholder="10"
                    />
                    <Button mt={25} onClick={handleRunXic} loading={loadingXic} disabled={!readySession}>
                      Run XIC
                    </Button>
                  </Group>
                </Group>
                {xic ? (
                  <Plot
                    data={[
                      {
                        x: xic.trace.map((point) => point.rt),
                        y: xic.trace.map((point) => point.intensity),
                        type: 'scattergl',
                        mode: 'lines',
                        line: { color: '#0891b2', width: 2.5 },
                        hovertemplate: 'RT %{x:.2f} min<br/>Intensity %{y:.3s}<extra></extra>',
                      },
                    ]}
                    layout={{
                      autosize: true,
                      height: 320,
                      margin: { l: 56, r: 20, t: 12, b: 52 },
                      paper_bgcolor: 'transparent',
                      plot_bgcolor: 'transparent',
                      xaxis: { title: { text: 'Retention time (min)' } },
                      yaxis: { title: { text: 'XIC intensity' } },
                    }}
                    config={{ displaylogo: false, responsive: true }}
                    style={{ width: '100%' }}
                  />
                ) : (
                  <div className="empty-state">
                    <IconDatabaseSearch size={34} />
                    <Text>Choose a target mass to compute an extracted ion chromatogram.</Text>
                  </div>
                )}
              </Card>
            </Grid.Col>
          </Grid>

          <Card withBorder radius="lg" padding="lg">
            <Group justify="space-between" mb="sm">
              <div>
                <Title order={3}>Spectrum at selected retention time</Title>
                <Text size="sm" c="dimmed">
                  Nearest scan to {selectedRtLabel}. Peak labels show the strongest local maxima.
                </Text>
              </div>
              {loadingSpectrum && <Loader size="sm" />}
            </Group>
            {spectrum ? (
              <Plot
                data={[
                  {
                    x: spectrum.mz,
                    y: spectrum.intensity,
                    type: 'scattergl',
                    mode: 'lines',
                    line: { color: '#111827', width: 1.5 },
                    hovertemplate: 'm/z %{x:.4f}<br/>Intensity %{y:.3s}<extra></extra>',
                  },
                  {
                    x: spectrum.peakLabels.map((peak) => peak.mz),
                    y: spectrum.peakLabels.map((peak) => peak.intensity),
                    text: spectrum.peakLabels.map((peak) => peak.mz.toFixed(4)),
                    type: 'scattergl',
                    mode: 'text+markers',
                    textposition: 'top center',
                    marker: { color: '#dc2626', size: 7 },
                    hovertemplate: 'Peak m/z %{x:.4f}<br/>Intensity %{y:.3s}<extra></extra>',
                  },
                ]}
                layout={{
                  autosize: true,
                  height: 420,
                  margin: { l: 56, r: 20, t: 12, b: 52 },
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'transparent',
                  xaxis: { title: { text: 'm/z' } },
                  yaxis: { title: { text: 'Intensity' } },
                  showlegend: false,
                }}
                config={{ displaylogo: false, responsive: true }}
                style={{ width: '100%' }}
              />
            ) : (
              <div className="empty-state">
                <IconScan size={34} />
                <Text>Pick a retention time from the TIC or map to inspect its mass spectrum.</Text>
              </div>
            )}
            {readySession?.datasetNotes && readySession.datasetNotes.length > 0 && (
              <List mt="md" size="sm">
                {readySession.datasetNotes.map((note) => (
                  <List.Item key={note}>{note}</List.Item>
                ))}
              </List>
            )}
          </Card>

          <Alert variant="light" color="gray" icon={<IconInfoCircle size={18} />}>
            <Text fw={600}>Thermo RAW conversion</Text>
            <Text size="sm" mt="xs">
              RAW conversion uses ThermoRawFileParser and the Thermo Fisher Scientific
              RawFileReader SDK. Copyright © 2016 Thermo Fisher Scientific, Inc. All rights
              reserved.
            </Text>
          </Alert>
        </Stack>
      </AppShell.Main>
    </AppShell>
  )
}

export default App
