#include <cstdint>
#include <cstddef>

namespace  NS1
{
struct S {
    void f(int i, float);
    void g(double d) const;
    void h(double d) volatile; // cannot detect volatile...
    constexpr void i(double d) ;

    virtual int pure() = 0;
    virtual int v();

    template <typename T, std::size_t N> void t(T element, unsigned u);

    S() = default;
};

struct S0 {
    virtual int v();
    virtual int pure();
};

struct S2 : S0 {
    int v() override;
    int pure() final;
    class C {
        C() = default;
    };
};

template <typename T, int N> struct array {
    void f();
    T tab[N];
};
}

