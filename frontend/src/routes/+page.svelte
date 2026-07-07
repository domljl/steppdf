<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import {
    ArrowDown,
    ArrowUp,
    Download,
    FilePlus2,
    FileText,
    Moon,
    Plus,
    Sun,
    Trash2,
    UploadCloud,
    XCircle,
  } from "@lucide/svelte";
  import { Alert, AlertDescription, AlertTitle } from "$lib/components/ui/alert/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Progress } from "$lib/components/ui/progress/index.js";
  import { Separator } from "$lib/components/ui/separator/index.js";
  import {
    extensionFor,
    maxFiles,
    maxTotalBytes,
    mergeOrder,
    moveEntry,
    validateFiles,
    type FileEntry,
  } from "$lib/file-state";

  type Job = {
    job_id: string;
    phase: string;
    percent: number;
    message: string;
    output_filename: string;
    error_detail: string | null;
  };

  type ChosenFile = FileEntry<File> & {
    previewUrl: string;
  };

  let fileInput = $state<HTMLInputElement>();
  let chosenFiles = $state<ChosenFile[]>([]);
  let nextFileId = $state(1);
  let outputFilename = $state("merged_by_dom.pdf");
  let fileMessage = $state("");
  let progressMessage = $state("Waiting for files.");
  let progressPercent = $state(0);
  let job = $state<Job | null>(null);
  let uploading = $state(false);
  let reducedMotion = $state(false);
  let darkMode = $state(false);
  let pollTimer: number | undefined;

  const hasFiles = $derived(chosenFiles.length > 0);
  const canSubmit = $derived(hasFiles && !uploading);

  function applyTheme(theme: "light" | "dark") {
    document.documentElement.classList.remove("light", "dark");
    document.documentElement.classList.add(theme);
    document.documentElement.style.colorScheme = theme;
    darkMode = theme === "dark";
    localStorage.setItem("theme", theme);
  }

  function initTheme() {
    const stored = localStorage.getItem("theme");
    const theme =
      stored === "light" || stored === "dark"
        ? stored
        : window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";

    applyTheme(theme);
  }

  function toggleTheme() {
    applyTheme(darkMode ? "light" : "dark");
  }

  function previewUrlFor(file: File) {
    return extensionFor(file) === "pdf" ? URL.createObjectURL(file) : "";
  }

  function revokePreview(entry: ChosenFile) {
    if (entry.previewUrl) URL.revokeObjectURL(entry.previewUrl);
  }

  function addFiles(files: File[]) {
    const message = validateFiles(chosenFiles, files);
    if (message) {
      fileMessage = message;
      return;
    }

    chosenFiles = [
      ...chosenFiles,
      ...files.map((file) => ({
        id: nextFileId++,
        file,
        previewUrl: previewUrlFor(file),
      })),
    ];
    fileMessage = "";
  }

  function handleFileInput() {
    addFiles(Array.from(fileInput?.files ?? []));
    if (fileInput) fileInput.value = "";
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    addFiles(Array.from(event.dataTransfer?.files ?? []));
  }

  function removeFile(fileId: number) {
    const removedFile = chosenFiles.find((entry) => entry.id === fileId);
    if (removedFile) revokePreview(removedFile);
    chosenFiles = chosenFiles.filter((entry) => entry.id !== fileId);
  }

  function clearFiles() {
    if (uploading) return;
    chosenFiles.forEach(revokePreview);
    chosenFiles = [];
    fileMessage = "";
    progressMessage = "Waiting for files.";
    progressPercent = 0;
    job = null;
    if (fileInput) fileInput.value = "";
    if (pollTimer) window.clearTimeout(pollTimer);
  }

  function moveFile(fromIndex: number, toIndex: number) {
    chosenFiles = moveEntry(chosenFiles, fromIndex, toIndex);
  }

  function showProgress(message: string, percent: number) {
    progressMessage = `${message} (${percent}%)`;
    progressPercent = percent;
  }

  async function pollJob(jobId: string) {
    const response = await fetch(`/jobs/${jobId}`);
    const nextJob: Job = await response.json();

    job = nextJob;
    showProgress(nextJob.message, nextJob.percent);

    if (!["ready", "failed", "expired"].includes(nextJob.phase)) {
      pollTimer = window.setTimeout(() => pollJob(nextJob.job_id), 500);
    }
  }

  function submitJob() {
    if (!canSubmit) return;

    const formData = new FormData();
    for (const entry of chosenFiles) formData.append("files", entry.file);
    formData.set("merge_order", mergeOrder(chosenFiles));
    formData.set("output_filename", outputFilename || "merged_by_dom.pdf");

    uploading = true;
    job = null;

    const xhr = new XMLHttpRequest();
    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) showProgress("Uploading", Math.round((event.loaded / event.total) * 100));
    });
    xhr.addEventListener("load", () => {
      uploading = false;
      if (xhr.status < 200 || xhr.status >= 300) {
        progressMessage = "Upload failed.";
        progressPercent = 100;
        return;
      }

      const createdJob: Job = JSON.parse(xhr.responseText);
      job = createdJob;
      showProgress(createdJob.message, createdJob.percent);
      pollJob(createdJob.job_id);
    });
    xhr.addEventListener("error", () => {
      uploading = false;
      progressMessage = "Upload failed.";
      progressPercent = 100;
    });
    xhr.open("POST", "/jobs");
    xhr.send(formData);
  }

  onMount(() => {
    reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    initTheme();
  });

  onDestroy(() => {
    if (pollTimer) window.clearTimeout(pollTimer);
    chosenFiles.forEach(revokePreview);
  });
</script>

<svelte:head>
  <title>StepPDF</title>
  <meta name="description" content="Convert decks and documents into one ordered PDF." />
</svelte:head>

<svelte:window ondragover={(event) => event.preventDefault()} ondrop={handleDrop} />

<div class="min-h-[100dvh] bg-background text-foreground">
  <header
    class="fixed inset-x-0 top-0 z-30 border-b border-[color-mix(in_srgb,var(--foreground)_10%,transparent)] bg-[color-mix(in_srgb,var(--background)_72%,transparent)] px-4 py-3 shadow-[0_8px_32px_rgba(0,0,0,0.16)] backdrop-blur-xl sm:px-8"
  >
    <a
      href="https://dominiclim.dev"
      class="absolute left-4 top-1/2 -translate-y-1/2 rounded-lg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent sm:left-8"
      aria-label="dominiclim.dev"
    >
      <img class="size-11 invert dark:invert-0 sm:size-14" src="/domLogo.svg" alt="" />
    </a>

    <div class="mx-auto flex max-w-7xl items-center justify-between gap-4">
      <a
        href="/"
        class="flex min-w-0 items-center gap-3 rounded-lg text-foreground no-underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        aria-label="StepPDF home"
      >
        <span class="size-11 shrink-0 sm:size-14" aria-hidden="true"></span>
        <span class="min-w-0">
          <span class="block text-2xl font-medium tracking-normal sm:text-4xl">StepPDF</span>
          <span class="hidden text-sm text-muted-foreground sm:block">
            Convert decks and documents into one ordered PDF.
          </span>
        </span>
      </a>

      <div class="flex shrink-0 items-center gap-2">
        <Badge variant="outline" class="hidden border-border bg-[color-mix(in_srgb,var(--foreground)_6%,transparent)] sm:inline-flex">
          Auto-deletes after 1 hour
        </Badge>
        <Button
          variant="outline"
          size="icon"
          aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
          onclick={toggleTheme}
          class="rounded-full bg-[color-mix(in_srgb,var(--foreground)_6%,transparent)]"
        >
          {#if darkMode}
            <Sun data-icon="inline-start" />
          {:else}
            <Moon data-icon="inline-start" />
          {/if}
        </Button>
      </div>
    </div>
  </header>

  <main class="min-h-[100dvh] pt-24">
    <form
      id="conversion-form"
      data-max-files={maxFiles}
      data-max-total-bytes={maxTotalBytes}
      class="min-h-[calc(100dvh-6rem)]"
      onsubmit={(event) => event.preventDefault()}
    >
      <input id="merge-order" name="merge_order" type="hidden" value={mergeOrder(chosenFiles)} />

      {#if !hasFiles}
        <section
          id="start-page"
          class="mx-auto grid min-h-[calc(100dvh-6rem)] w-full max-w-3xl place-items-center px-4 text-center"
        >
          <div class="grid justify-items-center gap-8">
            <div class="grid gap-4">
              <p class="text-2xl text-muted-foreground sm:text-3xl">
                Auto convert and combine PDFs in the order you want.
              </p>
            </div>

            <input
              bind:this={fileInput}
              class="sr-only"
              id="file-input"
              type="file"
              multiple
              accept=".pptx,.ppt,.docx,.pdf"
              onchange={handleFileInput}
            />
            <Button
              variant="outline"
              size="lg"
              class="!h-24 !gap-5 !rounded-full !px-14 !text-4xl !leading-none bg-[color-mix(in_srgb,var(--foreground)_6%,transparent)] shadow-[0_8px_32px_rgba(0,0,0,0.22)] transition-transform hover:ring-[color-mix(in_srgb,var(--accent)_35%,transparent)] [&_svg]:!size-9 sm:!h-28 sm:!gap-6 sm:!px-16 sm:!text-5xl sm:[&_svg]:!size-11 {reducedMotion ? '' : 'hover:scale-[1.03] active:scale-[0.97]'}"
              onclick={() => fileInput?.click()}
            >
              <UploadCloud data-icon="inline-start" />
              <span class="flex items-center leading-none">Browse files</span>
            </Button>

            <div class="grid gap-3 text-base text-muted-foreground sm:text-lg">
              <p>or drop files anywhere</p>
              <p>Accepted: PPTX, PPT, DOCX, and PDF. Files are automatically deleted after one hour.</p>
            </div>

            {#if fileMessage}
              <Alert variant="destructive" class="max-w-xl bg-[color-mix(in_srgb,var(--foreground)_6%,transparent)]">
                <XCircle />
                <AlertTitle>File check failed</AlertTitle>
                <AlertDescription>{fileMessage}</AlertDescription>
              </Alert>
            {/if}
          </div>
        </section>
      {:else}
        <section id="files-page" class="grid min-h-[calc(100dvh-6rem)] lg:grid-cols-[minmax(0,1fr)_24rem]">
          <section class="px-4 py-10 lg:px-10" aria-labelledby="selected-files-heading">
            <div class="mx-auto max-w-5xl">
              <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h1 class="text-2xl font-medium text-foreground" id="selected-files-heading">Selected files</h1>
                  <p class="mt-1 text-sm text-muted-foreground">Drag files to reorder them.</p>
                </div>
                <div class="flex flex-wrap gap-2">
                  <Button id="add-more-button" variant="outline" onclick={() => fileInput?.click()}>
                    <Plus data-icon="inline-start" />
                    Add more files
                  </Button>
                  <Button variant="outline" onclick={clearFiles} disabled={uploading}>
                    <Trash2 data-icon="inline-start" />
                    Clear all files
                  </Button>
                </div>
              </div>

              <input
                bind:this={fileInput}
                class="sr-only"
                id="file-input"
                type="file"
                multiple
                accept=".pptx,.ppt,.docx,.pdf"
                onchange={handleFileInput}
              />

              {#if fileMessage}
                <Alert variant="destructive" class="mb-5 bg-[color-mix(in_srgb,var(--foreground)_6%,transparent)]">
                  <XCircle />
                  <AlertTitle>File check failed</AlertTitle>
                  <AlertDescription>{fileMessage}</AlertDescription>
                </Alert>
              {/if}

              <ol id="selected-files" class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {#each chosenFiles as entry, index (entry.id)}
                  <li
                    class="grid cursor-grab gap-3 rounded-lg bg-[color-mix(in_srgb,var(--foreground)_6%,transparent)] p-4 text-sm shadow-[0_8px_32px_rgba(0,0,0,0.22)] ring-1 ring-[color-mix(in_srgb,var(--foreground)_10%,transparent)] active:cursor-grabbing"
                    draggable="true"
                    ondragstart={(event) => event.dataTransfer?.setData("text/plain", String(index))}
                    ondragover={(event) => event.preventDefault()}
                    ondrop={(event) => {
                      event.preventDefault();
                      event.stopPropagation();
                      moveFile(Number(event.dataTransfer?.getData("text/plain")), index);
                    }}
                  >
                    {#if entry.previewUrl}
                      <div
                        class="aspect-[3/4] overflow-hidden rounded-md bg-background ring-1 ring-[color-mix(in_srgb,var(--foreground)_10%,transparent)]"
                      >
                        <object
                          class="size-full pointer-events-none"
                          data={`${entry.previewUrl}#page=1&toolbar=0&navpanes=0&scrollbar=0`}
                          type="application/pdf"
                          aria-label={`Preview of ${entry.file.name}`}
                        >
                          <span class="grid size-full place-items-center text-sm font-medium uppercase text-muted-foreground">
                            pdf
                          </span>
                        </object>
                      </div>
                    {:else}
                      <div
                        class="grid aspect-[3/4] place-items-center rounded-md bg-[color-mix(in_srgb,var(--foreground)_8%,transparent)] text-sm font-medium uppercase text-muted-foreground ring-1 ring-[color-mix(in_srgb,var(--foreground)_10%,transparent)]"
                      >
                        {extensionFor(entry.file)}
                      </div>
                    {/if}
                    <span class="min-w-0 truncate text-center font-medium text-foreground">{entry.file.name}</span>
                    <div class="flex justify-center gap-2">
                      <Button variant="outline" size="icon-sm" disabled={index === 0} onclick={() => moveFile(index, index - 1)} aria-label="Move file up">
                        <ArrowUp data-icon="inline-start" />
                      </Button>
                      <Button
                        variant="outline"
                        size="icon-sm"
                        disabled={index === chosenFiles.length - 1}
                        onclick={() => moveFile(index, index + 1)}
                        aria-label="Move file down"
                      >
                        <ArrowDown data-icon="inline-start" />
                      </Button>
                      <Button variant="outline" size="icon-sm" onclick={() => removeFile(entry.id)} aria-label="Remove file">
                        <Trash2 data-icon="inline-start" />
                      </Button>
                    </div>
                  </li>
                {/each}
              </ol>
            </div>
          </section>

          <aside
            class="grid gap-5 border-l border-[color-mix(in_srgb,var(--foreground)_10%,transparent)] bg-[color-mix(in_srgb,var(--foreground)_4%,transparent)] p-5 lg:min-h-[calc(100dvh-6rem)] lg:grid-rows-[auto_auto_1fr_auto]"
          >
            <div class="text-center">
              <h2 class="text-2xl font-medium">Ready to merge</h2>
              <p class="mt-1 text-sm text-muted-foreground">{chosenFiles.length} file{chosenFiles.length === 1 ? "" : "s"}</p>
            </div>

            <Separator />

            <div class="grid content-start gap-5">
              <label class="grid gap-2">
                <span class="text-sm font-medium text-foreground">Output filename</span>
                <Input name="output_filename" bind:value={outputFilename} />
              </label>

              <section aria-labelledby="progress-heading" class="grid gap-2">
                <div class="flex items-center justify-between gap-3">
                  <h3 class="text-sm font-medium text-foreground" id="progress-heading">Progress</h3>
                  <Badge variant="secondary">{progressPercent}%</Badge>
                </div>
                <Progress value={progressPercent} />
                <div class="text-sm leading-6 text-muted-foreground" id="progress-panel">{progressMessage}</div>
              </section>

              {#if job?.phase === "failed"}
                <Alert variant="destructive" class="bg-[color-mix(in_srgb,var(--foreground)_6%,transparent)]">
                  <XCircle />
                  <AlertTitle>{job.message}</AlertTitle>
                  {#if job.error_detail}
                    <AlertDescription>
                      <details class="mt-3">
                        <summary class="cursor-pointer font-medium">Technical details</summary>
                        <pre class="mt-3 max-h-48 overflow-auto rounded-lg bg-[color-mix(in_srgb,var(--foreground)_6%,transparent)] p-3 text-sm text-foreground ring-1 ring-[color-mix(in_srgb,var(--foreground)_10%,transparent)]">{job.error_detail}</pre>
                      </details>
                    </AlertDescription>
                  {/if}
                </Alert>
              {/if}

              {#if job?.phase === "ready"}
                <Button href={`/jobs/${job.job_id}/download`} variant="outline" class="w-fit rounded-full">
                  <Download data-icon="inline-start" />
                  Download {job.output_filename}
                </Button>
              {/if}
            </div>

            <Button
              id="convert-button"
              size="lg"
              class="h-14 rounded-full text-xl transition-transform {reducedMotion ? '' : 'hover:scale-[1.03] active:scale-[0.97]'}"
              disabled={!canSubmit}
              onclick={submitJob}
            >
              {#if uploading}
                <FilePlus2 data-icon="inline-start" />
              {:else}
                <FileText data-icon="inline-start" />
              {/if}
              Merge PDF
            </Button>
          </aside>
        </section>
      {/if}
    </form>
  </main>
</div>
