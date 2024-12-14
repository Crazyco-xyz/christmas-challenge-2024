const API_PREFIX = "/a/v1";

class API {
  files = {};
  icons = [];
  names = {};
  dir = [];
  dirHistoryBack = [];
  dirHistoryFwd = [];

  constructor(initCallback) {
    this.#_listIcons(() => {
      this.#_listAllFiles(initCallback);
    });
  }

  /**
   * Requests the specified endpoint
   * @param {string} endpoint Endpoint to request
   * @param {{}} body The body to append
   * @param {Function} onSuccess Success callback
   * @param {Function} onFailure Failure callback
   */
  #_request(endpoint, body, onSuccess, onFailure, hasResponse = true) {
    this.#_requestData(
      endpoint,
      JSON.stringify(body),
      "application/json",
      onSuccess,
      onFailure,
      hasResponse
    );
  }

  /**
   * Uploads the given data to the backend and checks the response
   * @param {string} endpoint The endpoint to upload the data to
   * @param {*} data The data to upload
   * @param {string} dataType The MIME type of the data
   * @param {Function} onSuccess The success callback
   * @param {Function} onFailure The failure callback
   */
  #_requestData(
    endpoint,
    data,
    dataType,
    onSuccess,
    onFailure,
    hasResponse = true
  ) {
    const reqInit =
      data !== null
        ? {
            method: "POST",
            body: data,
            headers: {
              "Content-Type": dataType,
            },
          }
        : null;

    fetch(API_PREFIX + endpoint, reqInit)
      .then(async function (response) {
        return hasResponse // NOSONAR
          ? { status: response.ok, body: await response.json() }
          : { status: response.ok, body: {} };
      })
      .then(({ status, body }) => {
        if (status && onSuccess) onSuccess(body);
        if (!status && onFailure) onFailure(body);
      })
      .catch((e) => console.error("Could not request ", endpoint, e));
  }

  #_listIcons(onSuccess) {
    fetch("/s/filetypes.json")
      .then((response) => response.json())
      .then((json) => {
        this.icons = json;
        onSuccess();
      })
      .catch((e) => console.error("Could not retrieve file icons", e));
  }

  /**
   * Renews the name list
   * @param {*} [files = this.files] The parent element to start off from
   */
  #_listNames(files = this.files) {
    this.names = {};

    for (const id of Object.keys(files)) {
      if (typeof files[id] === "object") {
        this.#_listNames(files[id]);
        this.names[id] = files[id]._name;
        continue;
      }

      this.names[id] = files[id];
    }

    console.log(this.names);
  }

  /**
   * Requests a directory listing from the server
   * @param {Function} callback The function to callback when this function completed
   */
  #_listAllFiles(callback) {
    const onSuccess = (body) => {
      this.files = body;

      this.names = {};
      this.#_listNames(body);

      callback();
    };
    this.#_request("/listall", null, onSuccess);
  }

  /**
   * Moves into the specified directory
   * @param {string} dirId The ID of the dir
   */
  moveInto(dirId) {
    this.dirHistoryBack.push(this.dir.slice());
    this.dir.push(dirId);
  }

  /**
   * Moves out of the current directory
   */
  moveUp() {
    if (this.dir.length === 0) return;

    this.dirHistoryBack.push(this.dir.slice());
    this.dir.pop();
  }

  /**
   * Moves back one step
   */
  moveBack() {
    if (this.dirHistoryBack.length === 0) return;

    this.dirHistoryFwd.push(this.dir.slice());

    this.dir = this.dirHistoryBack.pop();
  }

  /**
   * Moves forward one step
   */
  moveForward() {
    if (this.dirHistoryFwd.length === 0) return;

    this.dirHistoryBack.push(this.dir.slice());

    this.dir = this.dirHistoryFwd.pop();
  }

  /**
   * Moves the view into the given directory
   * @param {[]} parts The path to this directory in ids
   */
  moveStatic(parts) {
    this.dirHistoryBack.push(this.dir.slice());

    this.dir = parts;
  }

  /**
   * @returns The file listing of the currently selected directory
   */
  currentDir() {
    let dir = this.files;

    for (const path of this.dir) {
      dir = dir[path];
    }

    return dir;
  }

  /**
   * @returns The full directory path of names
   */
  currentDirPath() {
    let fullPath = [],
      dir = this.files;

    for (const path of this.dir) {
      dir = dir[path];
      fullPath.push({ name: dir._name, id: path });
    }

    return fullPath;
  }

  /**
   * Queries the name of the current user
   * @param {Function} callback The success callback
   */
  userId(callback) {
    this.#_request("/user", null, (body) => callback(body.user_name));
  }

  /**
   * Uploads all given files to the server
   * @param {FileList} files The files to upload
   * @param {Function} onSuccess The success callback called for each file
   * @param {Function} onFailure The failure callback called for each file
   * @param {Function} onFinish The finish callback called once at the end
   */
  uploadFiles(files, onSuccess, onFailure, onFinish) {
    let remainingUploads = files.length;

    const finishOne = () => {
        // Mark this upload as finished and
        remainingUploads -= 1;
        if (remainingUploads === 0) onFinish();
      },
      makeURI = (name) => {
        if (this.dir.length === 0) return `/upload/${name}`;

        const dirId = this.dir[this.dir.length - 1];
        return `/upload/${dirId}/${name}`;
      },
      readFile = (file) => {
        const reader = new FileReader(),
          successCallback = (body) => {
            onSuccess(file.name, body);
            finishOne();
          },
          failureCallback = (body) => {
            onFailure(file.name, body);
            finishOne();
          };
        reader.onload = (event) => {
          // Trigger upload when file gets read
          const data = new Uint8Array(event.target.result);
          this.#_requestData(
            makeURI(file.name),
            data,
            "application/octet-stream",
            successCallback,
            failureCallback
          );
        };

        // Read the file from HDD
        reader.readAsArrayBuffer(file);
      };

    // Upload all selected files
    for (const file of files) readFile(file);
  }

  /**
   * Retrieves the name of a file from its id
   * @param {string} searchID The ID of the file
   * @returns The name of the file or null if not found
   */
  nameById(searchID) {
    return this.names[searchID];
  }

  /**
   * @returns The files stored at the root of the filesystem
   */
  root() {
    return this.files;
  }

  dirsIn(allFiles) {
    const dirs = {};

    for (const id of Object.keys(allFiles)) {
      if (typeof allFiles[id] === "object") dirs[id] = allFiles[id]._name;
    }

    return dirs;
  }

  filesIn(allFiles) {
    const files = {};

    for (const id of Object.keys(allFiles)) {
      if (typeof allFiles[id] !== "object") files[id] = allFiles[id];
    }

    return files;
  }

  /**
   * Creates a new folder inside the current directory
   * @param {string} name The name of the folder to create
   * @param {Function} onFinish The finish callback
   */
  createFolder(name, onFinish) {
    const dirId = this.dir.length === 0 ? "" : this.dir[this.dir.length - 1];

    this.#_request(
      "/folder",
      {
        parent_id: dirId,
        folder_name: name,
      },
      (body) => {
        const folderId = body.folder_id;

        this.currentDir()[folderId] = { _name: name };
        this.names[folderId] = name;

        onFinish(folderId);
      }
    );
  }

  /**
   * Renames a file
   * @param {string} fileId The id of the file
   * @param {string} newName The new name of the file
   */
  rename(fileId, newName) {
    this.#_request(
      "/rename",
      { file_id: fileId, new_name: newName },
      null,
      null,
      false
    );

    let curDir = this.currentDir();
    if (this.dirsIn(curDir)[fileId] === undefined) {
      curDir[fileId] = newName;
      return;
    }

    curDir[fileId]._name = newName;
  }

  /**
   * Deletes a file
   * @param {string} fileId The id of the file
   */
  delete(fileId) {
    this.#_request("/delete", { file_id: fileId }, null, null, false);
    delete this.currentDir()[fileId];
  }

  /**
   * Retrieves an icon from the filename
   * @param {string} name The name of the file
   * @returns The class name of the icon
   */
  iconByName(name) {
    let parts = name.split("."),
      extention = parts[parts.length - 1].toLowerCase();

    for (const type of this.icons) {
      if (type.ext.includes(extention)) {
        return type.icon;
      }
    }

    return "fa-file";
  }
}

export { API };
