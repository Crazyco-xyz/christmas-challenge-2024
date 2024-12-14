class Abortable {
  static abortCallback = null;
  callback;

  constructor(callback) {
    this.callback = callback;
  }

  static abort(e) {
    if (e) e.stopPropagation();

    if (Abortable.abortCallback) Abortable.abortCallback.callback();
    Abortable.abortCallback = null;
  }

  static add(callback) {
    Abortable.abortCallback = new Abortable(callback);
  }
}

export default Abortable;
