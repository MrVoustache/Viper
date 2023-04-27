"""
When loaded, this module allows the use of procedural packages:

A procedural packaga is much more complex than a regular Python package.
Just like a normal package, a procedural package is a folder used (usually to store submodules/subpackages), but unlike them, an "__init__.py" file is not required, a "__proc__.py" file is.

The goal of this "__proc__.py" script is to define procedures to handle the package.
When this script is executed, is is done in the namespace of the package and a special value is given under the variable "__proc__". It contains a "ProcedureDescriptor" object which allows to describe:
    - What to do when the package is first loaded.
    - What to do when all submodules/subpackages have been loaded.
    - What to do before and after loading a submodule/subpackage.
For more information on these customizations, look at the "ProcedureDescriptor" class in this module. It describes all the specializations that can be done for procedural packages.

Just note that you should avoid loading submodules/subpackages in the "__proc__.py" script as it could have unpredicted behaviors. Do that in an "__init__.py" script instead.
"""

from importlib.abc import Loader
from importlib.machinery import ModuleSpec, PathFinder
from pathlib import Path
import sys
from types import ModuleType
from typing import Sequence
from weakref import WeakValueDictionary

__all__ = ["ProcedureError", "ProcedureDescriptor", "ProceduralImporter"]





class ProcedureError(ImportError):

    """
    This error indicates that the import of a procedural package failed because the package __proc__.py file is missing a procedure (a "__proc__" variable with an object of type 'ProcedureDescriptor').
    """





class ProcedureDescriptor:

    """
    A class to explain how to load a procedural package.
    A procedural package contains a __proc__.py script at its root and has one of these objects under the variable "__proc__".

    This object contain multiple properties allowing you to explain the procedure to load the package.
    """

    __slots__ = {
        "__package" : "The path to the package folder",
        "__init" : "The path to the file to run at the time the package is first imported",
        "__init_module" : "The path to the file to run at each time a sub-package/module is imported",
        "__term_module" : "The path to the file to run at each time a sub-package/module has been imported",
        "__term" : "The path to the file to run when all sub-packages/modules have been imported (requires an '__all__' list)"
    }

    def __init__(self, package_path : Path) -> None:
        from pathlib import Path
        from importlib.machinery import SOURCE_SUFFIXES
        self.__package : Path = package_path
        module_files = {p.with_suffix("").name : p for p in package_path.iterdir() if p.suffix in SOURCE_SUFFIXES}
        self.__init : Path | None = None if "__init__" not in module_files else module_files["__init__"]
        self.__init_module : Path | None = None if "__init_module__" not in module_files else module_files["__init_module__"]
        self.__term_module : Path | None = None if "__term_module__" not in module_files else module_files["__term_module__"]
        self.__term : Path | None = None if "__term__" not in module_files else module_files["__term__"]
    
    def __repr__(self) -> str:
        """
        Implements repr(self).
        """
        names : dict[str, str] = {}
        if self.init:
            names["init"] = self.init
        if self.init_module:
            names["init_module"] = self.init_module
        if self.term_module:
            names["term_module"] = self.term_module
        if self.term:
            names["term"] = self.term
        if not names:
            return "ProcedureDescriptor({})".format(self.__package)
        else:
            return "ProcedureDescriptor({}, {})".format(self.__package, ", ".join("{} : {}".format(name, p) for name, p in names.items()))

    @property
    def init_path(self) -> Path | None:
        """
        The path to the init script.
        """
        return self.__init

    @property
    def init(self) -> str:
        """
        The local module name to the init script (defaults to "__init__" for __init__.py if it exists) that should be run when the package is imported for the first time.
        The code in this script will share the namespace of the package.
        """
        return self.__init.with_suffix("").name if self.__init else ""
    
    @init.setter
    def init(self, name : str):
        from pathlib import Path
        if not isinstance(name, str):
            raise TypeError("Expected str, got " + repr(type(name).__name__))
        if name:
            self.__init = self.__package / Path(*name.split(".")).with_suffix(".py")
        else:
            self.__init = None
    
    @init.deleter
    def init(self):
        self.__init = None

    @property
    def term_path(self) -> Path | None:
        """
        The path to the term script.
        """
        return self.__term

    @property
    def term(self) -> str:
        """
        The local module name to the term script (defaults to "__term__" for __term__.py if it exists) that should be run when all modules/packages listed in the package's '__all__' list have been imported.
        The code in this script will share the namespace of the package.
        """
        return self.__term.with_suffix("").name if self.__term else ""
    
    @term.setter
    def term(self, name : str):
        from pathlib import Path
        if  not isinstance(name, str):
            raise TypeError("Expected str, got " + repr(type(name).__name__))
        if name:
            self.__term = self.__package / Path(*name.split(".")).with_suffix(".py")
        else:
            self.__term = None

    @term.deleter
    def term(self):
        self.__term = None

    @property
    def init_module_path(self) -> Path | None:
        """
        The path to the module init script.
        """
        return self.__init_module
    
    @property
    def init_module(self) -> str:
        """
        The local module name to the module init script (defaults to "__init_module__" for __init_module__.py if it exists) that should be run before each sub-module or sub-package import.
        The code in this script will share the namespaces of each sub-package/module.
        """
        return self.__init_module.with_suffix("").name if self.__init_module else ""
    
    @init_module.setter
    def init_module(self, name : str):
        from pathlib import Path
        if not isinstance(name, str):
            raise TypeError("Expected str, got " + repr(type(name).__name__))
        if name:
            self.__init_module = self.__package / Path(*name.split(".")).with_suffix(".py")
        else:
            self.__init_module = None

    @init_module.deleter
    def init_module(self):
        self.__init_module = None

    @property
    def term_module_path(self) -> Path | None:
        """
        The path to the term module script.
        """
        return self.__term_module

    @property
    def term_module(self) -> str:
        """
        The local module name to the module term script (defaults to "__term_module__" for __term_module__.py if it exists) that should be run after each sub-module or sub-package import.
        The code in this script will share the namespaces of each sub-package/module.
        """
        return self.__term_module.with_suffix("").name if self.__term_module else ""
    
    @term_module.setter
    def term_module(self, name : str):
        from pathlib import Path
        if not isinstance(name, str):
            raise TypeError("Expected str, got " + repr(type(name).__name__))
        if name:
            self.__term_module = self.__package / Path(*name.split(".")).with_suffix(".py")
        else:
            self.__term_module = None

    @term_module.deleter
    def term_module(self):
        self.__term_module = None





class ProceduralImporter(PathFinder, Loader):

    """
    A Finder and Loader which looks for procedural packages. These packages are indentified by a "__proc__.py" file instead of a "__init__.py" file.
    """

    __loaded_packages : WeakValueDictionary[str, ModuleType] = WeakValueDictionary()        # Procedural packages that have been loaded     (to react to their sub-modules)
    __loading_packages : dict[str, Path] = {}                                               # Procedural packages that are about to be imported     (to react when executing it)
    __package_all_remaining : dict[str, set[str]] = {}                                      # The list of sub-packages/modules that need to be loaded for a given procedural package

    __cache : dict[str, ModuleSpec] = {}


    def __init__(self, original_loader : Loader | None) -> None:
        super().__init__()
        self.__original_loader = original_loader


    @classmethod
    def find_spec(cls, fullname: str, path: Sequence[str] | None, target : ModuleType | None = None) -> ModuleSpec | None:

        if fullname in ProceduralImporter.__cache and not target:
            return ProceduralImporter.__cache[fullname]

        package, _, module = fullname.rpartition(".")
        spec = super().find_spec(fullname, path, target)

        if spec:

            # print("Trying to import '{}', got '{}'".format(fullname, spec))

            spec.loader = cls(spec.loader)
                    
            from pathlib import Path
            import sys
            directories = [Path(p) for p in (sys.path if path is None else path)]
            
            for dir in directories:
                package_dir = dir / module
                if package_dir.is_dir():
                    for file in package_dir.iterdir():
                        if file.name == "__proc__.py":
                            # print("Got a special package")
                            ProceduralImporter.__loading_packages[fullname] = file
                            break
            
            ProceduralImporter.__cache[fullname] = spec

        return spec
    

    @staticmethod
    def invalidate_caches():
        ProceduralImporter.__cache.clear()


    def create_module(self, spec: ModuleSpec) -> ModuleType | None:
        return None
    

    def exec_module(self, module: ModuleType) -> None:

        from pathlib import Path
        from types import CodeType


        def find_compile_or_load(fullname : str, path : Path) -> CodeType:
            """
            Searches for the given module (from its name and path), if a cache is available, loads the bytecode, else, compiles sources and saves bytecode.
            """
            code = None

            try:
                from importlib.util import cache_from_source
                from importlib.machinery import SourcelessFileLoader
                from py_compile import compile as compile_cache

                cache_path = Path(cache_from_source(str(path)))

                if cache_path.exists() and not cache_path.is_file():
                    return compile(path.read_text(), path, "exec")

                if not cache_path.is_file() or path.stat().st_mtime_ns > cache_path.stat().st_mtime_ns:
                    compile_cache(str(path), str(cache_path), doraise=True)
                
                loader = SourcelessFileLoader(fullname, str(cache_path))

                try:
                    code = loader.get_code(fullname)
                except ImportError:
                    code = None
            
            except:
                pass

            if not code:
                code = compile(path.read_text(), path, "exec")

            return code


        spec = module.__spec__
        if not spec:
            return super().exec_module(module)
        
        init = None
        module_init = None
        module_term = None
        parent_package = None
        term = None
        parent_term = None
        parent_spec : ProcedureDescriptor | None = None
        
        parent_name, _, module_name = module.__name__.rpartition(".")
        if parent_name and parent_name in ProceduralImporter.__loaded_packages:     # Parent package is procedural, register its __init_module__ and __term_module__
            parent_package = ProceduralImporter.__loaded_packages[parent_name]
            stupid_proc : ProcedureDescriptor = parent_package.__proc__
            parent_spec = stupid_proc
            module_init = parent_spec.init_module_path
            module_term = parent_spec.term_module_path
            parent_term = parent_spec.term_path


        if module_init and parent_spec:     # Parent is procedural with an init_module script
            code = find_compile_or_load(parent_name + "." + parent_spec.init_module, module_init)
            exec(code, module.__dict__)


        if module.__spec__ and module.__name__ in ProceduralImporter.__loading_packages:        # This is procedural package! Special handling.

            # First, find its __proc__ file
            proc_path = ProceduralImporter.__loading_packages[module.__name__]
            if not proc_path:
                raise ProcedureError("Procedural package got destroyed before being imported.")
            
            proc = ProcedureDescriptor(proc_path.parent)
            module.__proc__ = proc              # type: ignore          # New attrtibute of procedural packages...

            # Second, register it as an active procedural package
            ProceduralImporter.__loaded_packages[module.__name__] = module

            # Third, execute its __proc__ script and retrieve the procedure object
            
            code = find_compile_or_load(module.__name__ + ".__proc__", proc_path)
            exec(code, module.__dict__)

            if not hasattr(module, "__proc__"):
                raise ProcedureError("'__proc__.py' file of package '{}' does not have a '__proc__' name".format(module.__name__))
            
            proc : ProcedureDescriptor = module.__proc__
            if not isinstance(proc, ProcedureDescriptor):
                raise ProcedureError("'__proc__' attribute of package '{}' is not an instance of 'ProcedureDescriptor', got '{}'".format(module.__name__, type(proc).__name__))

            # Then, execute its init script
            init = proc.init_path

            if init:
                code = find_compile_or_load(module.__name__ + "." + proc.init, init)
                exec(code, module.__dict__)

            # If it has an "__all__" attribute, save its content for detection
            term = proc.term_path
            if hasattr(module, "__all__") and isinstance(module.__all__, list) and term:
                package_all = set(module.__all__)
                package_all.difference_update(module.__dict__)      # Remove names in __all__ that are already defined in the module.
                ProceduralImporter.__package_all_remaining[module.__name__] = package_all

                if not module.__all__:     # __all__ is defined but is an empty list...
                    code = find_compile_or_load(module.__name__ + "." + proc.term, term)
                    exec(code, module.__dict__)
                    ProceduralImporter.__package_all_remaining.pop(module.__name__)


        else:                                                               # Normal package. Load normally.

            if self.__original_loader:
                self.__original_loader.exec_module(module)
            else:
                super().exec_module(module)


        if module_term and parent_spec:         # Parent package is procedural with a term_module script
            code = find_compile_or_load(parent_name + "." + parent_spec.term_module, module_term)
            exec(code, module.__dict__)
        
        if parent_name in ProceduralImporter.__package_all_remaining:       # Parent package is procedural and has a term script. Check for completion
            ProceduralImporter.__package_all_remaining[parent_name].difference_update(module.__dict__)
            ProceduralImporter.__package_all_remaining[parent_name].discard(module_name)

            if not parent_term or not parent_package:
                raise RuntimeError("Got a termination registered sub-package without procedural parent with a term module")
            
            if not ProceduralImporter.__package_all_remaining[parent_name] and parent_spec:     # Parent package has its environment complete : run its term script.
                code = find_compile_or_load(parent_name + "." + parent_spec.term, parent_term)
                exec(code, parent_package.__dict__)
                ProceduralImporter.__package_all_remaining.pop(parent_name)
                    




sys.meta_path[-1] = ProceduralImporter      # Replace the source finder

del Loader, ModuleSpec, PathFinder, Path, sys, ModuleType, Sequence, WeakValueDictionary