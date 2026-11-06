from pathlib import Path
import ctypes,importlib.util,json,os,tempfile,threading,unittest

spec=importlib.util.spec_from_file_location('io_wrapper',Path(__file__).resolve().parents[1]/'scripts/collect_hidden_resumable.py')
wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper)

class AtomicProgress(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt','Windows file-sharing regression')
    def test_reader_without_delete_sharing_is_retried(self):
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
        kernel.CreateFileW.restype=ctypes.c_void_p
        kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        temp_root=Path(__file__).resolve().parents[1]/'build/atomic_tests'
        temp_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as folder:
            assert Path(folder).resolve().is_relative_to(temp_root.resolve())
            path=Path(folder)/'PROGRESS.json';path.write_text('{"completed":1}',encoding='utf-8')
            handle=kernel.CreateFileW(str(path),0x80000000,3,None,3,0x80,None)
            self.assertNotEqual(handle,ctypes.c_void_p(-1).value)
            before=wrapper.IO_STATS['retries']
            timer=threading.Timer(.1,lambda:kernel.CloseHandle(handle));timer.start()
            try:wrapper.atomic_write(path,dict(completed=2));timer.join()
            finally:
                if timer.is_alive():timer.join()
            self.assertEqual(json.loads(path.read_text())['completed'],2)
            self.assertGreater(wrapper.IO_STATS['retries'],before)

if __name__=='__main__':unittest.main()
