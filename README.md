# Readme

This is my entry to the [2024 Christmas Coding Challenge by CrazyCo](CHALLENGE.md). If you just want to run this
application yourself and not read tons of text, feel free to head down to [How to run](#how-to-run).

For all others, I have written my approach to this project, what I decided to focus on and my thoughts bethind the
implementation below. _Have fun reading!_

## Architecture

### How are the files stored?

I decided pretty early that I wanted to go with a hybrid approach for file storage. This means, storing all
properties belonging to the file inside a database and storing the actual file data directly on disk. This approach
makes file lookup way faster than if storing the binary data inside the database, which would bloat one file into
extremes.

Storing all files in one folder can lead to problems tho, but on modern file systems like `NTFS` or `ext4` this
should only happen when storing millions of files. More about this [below](#many-files-in-one-folder)!

### Why did I use Python?

I mainly used Python because it can run on many systems without problems. Obviously the uncompiled nature of Python
makes the application slower than compiled languages. Not needing to compile the project also means there is only one
version of the application which can run on many different environments, unlike compiled languages where you would
need one binary for each platform.

## Libraries

I wanted to use as few libraries as possible, because I got intrigued by the the `Dependencies` section of the
[Judging Criteria](CHALLENGE.md#-judging-criteria) and I like implementing protocols myself anyways. Pretty early it
was clear that I didn't want any external libraries in this project and I only allowed myself to use a few of the
internal libraries which Python has out of the box. If you want to learn more about all libraries I used, you can
take a look at the [libraries document](LIBRARIES.md) containing more information.

The only external library I allowed myself to use was [FontAwesome](https://github.com/FortAwesome/Font-Awesome)
which provided the icons I used in the frontend. The whole backend runs without needing any external libraries and
the rest of the frontend is written in vanilla `HTML`, `CSS` and `JS`.

The HTTPS interface runs using the `ssl` python library. The only problem with this approach is that the library
doesn't generate any keys or certificates that are neccecary for HTTPS to work. Because of this, I decided to
utilize the `openssl` command line utility that comes either with the standard Linux system utilities or with GIT
on Windows. Yes, this is kind of cheating my own goal, but I didn't feel like implementing this myself, mostly
without relying on any other libraries.

If you want to use your own certificate and private RSA key, you can do so by putting them in the root directory of
this project and naming them `key.pem` and `cert.pem` respectively. After a restart of the backend, they should get
loaded automatically.

## Web Interface

As stated before I wrote the whole frontend in vanilla `HTML`, `CSS` and `JS`. Using any libraries here would
defeat the whole purpose of this project, because the frontend mostly relies on the backend which gives it all
neccecary data for it to operate.

After starting the backend you can find the frontend interface by using your browser to go to the IP address where
the server which is running the backend is located. You can access the interface using `HTTP` or `HTTPS`, but when
using a self-signed certificate, the browser might complain when using `HTTPS`. In the development environment this
can savely be ignored.

After logging in, you will find the file picker in which you can see all your uploaded files. In the beginning this
will be empty, but you can upload files using the upload box in the bottom left. For creating folders, you
click on the `Create Folder` icon located at the end of the file listing.

Files can be opened/previewed by double-clicking on them, just like folders. More options are available by
right-clicking on files or folders. The sidebar on the left shows you a quick access to the folders located in the
root directory of your file storage.

When previewing a file, you can generate a share link by clicking the `Share` button. This will generate a link
with which anyone can access the file. You can protect this link using a password or leave it open for everyone to
see.

For the design I took inspiration on the [Notion](https://notion.so) web interface. I still tried to keep the
design original, but you might see a few similarities.

## WebDAV

I also implemented a WebDAV server which runs on the same ports as HTTP/HTTPS. You can use basically any software
which supports the WebDAV protocol, like `WinSCP` or `FileZilla`. As an important note,
**Windows Explorer is not supported**.

### Windows Explorer

I personally chose to not support Windows Explorer, because after implementing the WebDAV protocol I noticed, that
Explorer does not follow the protocol as defined in [RFC 4918](https://datatracker.ietf.org/doc/html/rfc4918). This
lead to hours of debugging without any results. Even other servers supporting WebDAV do not completely work
with Windows Explorer, for example [CivetWeb](https://github.com/civetweb/civetweb) as discussed in
[this issue](https://github.com/civetweb/civetweb/issues/1040).

As of now, Windows Explorer only partially works. Opening and deleting already existing files should work. Renaming
or moving a file works, even though Explorer raises an error. After closing this error popup and reloading the
directory, the rename or move should be visible. Uploading files does not work at all.

**Important:** A little side note here is that the file manager in GNOME, which also has WebDAV capabilities works
completely. Other file managers of Linux desktop environments have yet to be tested, but I assume they should also
work.

## How to run

**Only Python versions 3.12 and above work! Please upgrade from any version below!**

### Tested environments

The following environments have been tested and fully work:

- **Debian 12.8.0 on x86-64**

  ⇨ Installed with standard system utilities and upgraded from Python 3.11 to 3.12

- **Fedora 41 Workstation**

  ⇨ Additionally installed openssl using package manager

- **Ubuntu 20.04.6 LTS**

  ⇨ Installed openssl using package manager and upgraded from Python 3.8 to 3.12.

  <small>_Make sure, all standard python libraries get installed!_</small>

- **Windows 11 23H2**

  ⇨ Installed Python 3.12, installed GIT and added `C:\Program Files\Git\usr\bin` to PATH

### Startup

If you are on **Linux**, you need to run the `run.sh` file using sudo, because otherwise the application cannot use
the ports `80` and `443`. To change the ports used and not use sudo, you can edit the `src/constants.py` file.

To start the backend, simply follow the commands below depending your operating system. Upon first startup, the
script will generate a private RSA key and a self-signed certificate which will be used for HTTPS. You can savely
ignore the output of this process.

When started up successfully, you should see the following log messages. After this, the backend started up
successfully and you can access the frontend interface like [described above](#web-interface).

```text
[I] Starting server on 0.0.0.0:80
[I] Starting server on 0.0.0.0:443
```

Stopping the application can be achieved using <kbd>Ctrl</kbd> + <kbd>C</kbd>. Any file upload in progress will
immediately be stopped which might result in partial files. _Be careful!_

#### Linux

```bash
git clone https://github.com/JoaStuart/christmas-challenge-2024.git
cd christmas-challenge-2024
chmod +x ./run.sh
sudo ./run.sh
```

#### Windows

```ps1
git clone https://github.com/JoaStuart/christmas-challenge-2024.git
cd christmas-challenge-2024
./run.bat
```

## Known problems

### Public access

Everyone having access to the web interface can upload as many files as they please which might quickly lead to no
more space on the disk and/or high CPU usage. Be careful where you expose the IP.

### Compressed data

The server supports receiving compressed data, which might lead to zip-bomb like problems where the server tries to
decompress a few hundred TB of data.

### Denial of service

Rate limitation is yet to be implemented, meaning the server accepts every request and tries to fulfill it. Again,
be careful where you expose the IP.

### Many files in one folder

The storage architecture keeps all uploaded files inside one folder, which might lead to problems when storing
multiple millions of files on modern file systems. An important note here is that older file systems don't handle
this many files inside one folder this gracefully. For example FAT32 or exFAT might suffer with less files stored.

## Unimplemented features

- Own implementation of the SSL protocol, mimetype guessing and a JSON parser
- More advanced file sharing or sharing of files only with specified users
